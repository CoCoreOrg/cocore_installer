import sys
import asyncio
import json
import ssl
import requests
import websockets
from cryptography.fernet import Fernet
import traceback
import time
import subprocess

AUTH_KEY_FILE = "/etc/cocore/auth_key"
SECRET_KEY_FILE = "/etc/cocore/secret.key"
WEBSOCKET_SERVER = "wss://cocore.io/cable"
CERT_DIR = "/etc/cocore/certificates"
CLIENT_CERT_FILE = f"{CERT_DIR}/client.crt"
CLIENT_KEY_FILE = f"{CERT_DIR}/client.key"
CA_CERT_FILE = f"{CERT_DIR}/ca.crt"
TOKEN_PATH = "/etc/cocore/tokenfile"

def load_auth_key():
    try:
        with open(SECRET_KEY_FILE, "rb") as key_file:
            key = key_file.read()
        cipher_suite = Fernet(key)
        with open(AUTH_KEY_FILE, "rb") as file:
            encrypted_key = file.read()
        auth_key = cipher_suite.decrypt(encrypted_key).decode()
        print(f"Auth Key: {auth_key}")  # Add this line for debugging
        return auth_key
    except Exception as e:
        print(f"Error loading auth key: {e}")
        print(traceback.format_exc())
        sys.exit(1)

def send_specs(token, cpu, ram):
    payload = {
        "token": token,
        "cpu": cpu,
        "ram": ram
    }

    cmd = [
        'curl',
        '-X', 'POST',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps(payload),
        'https://cocore.io/hosts/update_specs'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    response = json.loads(result.stdout)

    if result.returncode == 0 and response.get("success"):
        print("Specifications updated successfully.")
    else:
        print(response.get("message"))

def get_system_resources():
    total_cpus = psutil.cpu_count(logical=True)
    total_memory = psutil.virtual_memory().total // (1024 * 1024)  # Convert bytes to MiB
    return total_cpus, total_memory

async def connect_and_subscribe(auth_type):
    ssl_context = ssl.create_default_context()
    ssl_context.load_cert_chain(certfile=CLIENT_CERT_FILE, keyfile=CLIENT_KEY_FILE)
    ssl_context.load_verify_locations(cafile=CA_CERT_FILE)
    ssl_context.verify_mode = ssl.CERT_REQUIRED

    auth_key = load_auth_key()
    headers = {
        "Authorization": f"Bearer {auth_key}",
        "Auth-Type": auth_type
    }

    retry_attempts = 0
    max_retries = 10

    while retry_attempts < max_retries:
        try:
            websocket = await websockets.connect(WEBSOCKET_SERVER, ssl=ssl_context, extra_headers=headers)
            print("Connected to WebSocket server")

            # Subscribe to the HostChannel
            subscribe_message = {
                "command": "subscribe",
                "identifier": json.dumps({"channel": "HostChannel"})
            }
            await websocket.send(json.dumps(subscribe_message))

            # Wait for the subscription confirmation
            while True:
                response = await websocket.recv()
                print(f"Received: {response}")
                response_data = json.loads(response)

                if response_data.get("type") == "confirm_subscription":
                    print("Subscription confirmed.")
                    subscription_id = response_data.get("identifier")
                    break

            return websocket, subscription_id
        except Exception as e:
            print(f"Connection failed: {e}")
            print(traceback.format_exc())
            retry_attempts += 1
            sleep_time = min(2 ** retry_attempts, 60)  # Exponential backoff with cap at 60 seconds
            print(f"Retrying in {sleep_time} seconds...")
            await asyncio.sleep(sleep_time)

    print("Max retry attempts reached. Exiting.")
    return None, None

async def fetch_task_execution(execution_id):
    try:
        url = f"https://cocore.io/task_executions/{execution_id}.json"
        headers = {
            "Authorization": f"Bearer {load_auth_key()}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to fetch task execution: {response.status_code}")
    except Exception as e:
        print(f"Error fetching task execution: {e}")
        print(traceback.format_exc())
        raise

def run_task(task_code, args):
    try:
        local_scope = {}
        exec(task_code, {}, local_scope)
        if 'run' in local_scope:
            start_time = time.perf_counter_ns()
            result = local_scope['run'](*args)
            end_time = time.perf_counter_ns()
            execution_time_microseconds = (end_time - start_time) / 1000
            print(f"Task executed in {execution_time_microseconds} microseconds")
            return {"result": result, "execution_length": execution_time_microseconds}
        else:
            return {"error": "NoRunFunction", "error_message": "No run() function defined, failed to execute!"}
    except Exception as e:
        error_context = {"error": str(e), "error_message": "Your code failed to complete because of an error.", "error_details": {}}
        for attr in ["__cause__", "__context__", "args", "__traceback__"]:
            if attr in dir(e):
                if attr == "__traceback__":
                    error_context["error_details"][attr] = '\n'.join(traceback.format_tb(getattr(e, attr)))
                else:
                    error_context["error_details"][attr] = str(getattr(e, attr))
        return error_context

async def process_task_execution(execution_id):
    try:
        task_execution = await fetch_task_execution(execution_id)
        task_code = task_execution['task']['code']
        input_args = task_execution['input'] or []

        result = run_task(task_code, input_args)

        # Post the result back to the server
        result_url = f"https://cocore.io/task_executions/{execution_id}"
        headers = {
            "Authorization": f"Bearer {load_auth_key()}",
            "Content-Type": "application/json"
        }
        payload = {
            "task_execution": result
        }
        response = requests.patch(result_url, headers=headers, json=payload)
        if response.status_code == 200:
            print("Task result posted successfully")
        else:
            print(f"Failed to post task result: {response.status_code}")
    except Exception as e:
        print(f"Error processing task execution: {e}")
        print(traceback.format_exc())
        raise

async def fetch_next_task_execution():
    try:
        url = "https://cocore.io/task_executions/next.json"
        headers = {
            "Authorization": f"Bearer {load_auth_key()}",
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None  # No task execution found
        else:
            raise Exception(f"Failed to fetch next task execution: {response.status_code}")
    except Exception as e:
        print(f"Error fetching next task execution: {e}")
        print(traceback.format_exc())
        raise

async def process_all_pending_tasks():
    while True:
        try:
            task_execution = await fetch_next_task_execution()
            if task_execution is None:
                print("No more pending task executions found.")
                break
            execution_id = task_execution['id']
            await process_task_execution(execution_id)
            await asyncio.sleep(1)  # Add delay to avoid spamming the server
        except Exception as e:
            print(f"Error processing pending tasks: {e}")
            print(traceback.format_exc())

async def send_keep_alive(websocket, subscription_id, interval=30):
    while True:
        try:
            await asyncio.sleep(interval)  # Adjust the interval as needed
            keep_alive_message = {
                "command": "message",
                "identifier": subscription_id,
                "data": json.dumps({"action": "keep_alive"})
            }
            await websocket.send(json.dumps(keep_alive_message))
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Error sending keep-alive message: {e}")
            break

async def task_listener(auth_type):
    while True:
        websocket, subscription_id = await connect_and_subscribe(auth_type)
        if not websocket:
            print("Exiting due to unsuccessful WebSocket connection.")
            return

        print('\nVM is ready to accept tasks. :)\n')
        sys.stdout.flush()

        keep_alive_task = asyncio.create_task(send_keep_alive(websocket, subscription_id))

        try:
            async for message in websocket:
                print('Got message: ' + message)
                response_data = json.loads(message)
                message = response_data.get("message", {})
                if isinstance(message, dict) and message.get("type") == "execute_task":
                    execution_id = response_data.get("message", {}).get("execution_id")
                    await process_task_execution(execution_id)
                else:
                    print(f"Unhandled message type: {response_data}")
                await process_all_pending_tasks()
        except websockets.ConnectionClosed:
            print("Connection closed, reconnecting...")
            keep_alive_task.cancel()
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Error processing task: {e}")
            keep_alive_task.cancel()
            print(traceback.format_exc())

async def main(auth_type):
    total_cpus, total_memory = get_system_resources()

    # Load the token
    with open(TOKEN_PATH, "r") as token_file:
        token = token_file.read().strip()

    send_specs(token, total_cpus, total_memory)

    websocket, subscription_id = await connect_and_subscribe(auth_type)
    if not websocket:
        print("Exiting due to unsuccessful WebSocket connection.")
        return
    await process_all_pending_tasks()  # Process all pending tasks on boot
    await task_listener(auth_type)  # Start listening for new tasks

if __name__ == "__main__":
    auth_type = "host"  # or "user" based on your context
    asyncio.run(main(auth_type))
