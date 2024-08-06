import time
import json
import asyncio
import websockets
import ssl
import sys
from cryptography.fernet import Fernet

AUTH_KEY_FILE = "/etc/cocore/auth_key"
SECRET_KEY_FILE = "/etc/cocore/secret.key"
WEBSOCKET_SERVER = "wss://cocore.io/cable"
CERT_DIR = "/etc/cocore/certificates"
CLIENT_CERT_FILE = f"{CERT_DIR}/client.crt"
CLIENT_KEY_FILE = f"{CERT_DIR}/client.key"
CA_CERT_FILE = f"{CERT_DIR}/ca.crt"

def load_auth_key():
    with open(SECRET_KEY_FILE, "rb") as key_file:
        key = key_file.read()
    cipher_suite = Fernet(key)
    with open(AUTH_KEY_FILE, "rb") as file:
        encrypted_key = file.read()
    return cipher_suite.decrypt(encrypted_key).decode()

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

    try:
        async with websockets.connect(WEBSOCKET_SERVER, ssl=ssl_context, extra_headers=headers) as websocket:
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
                    break

            # Send the ping command after subscription confirmation
            ping_message = {
                "command": "message",
                "identifier": json.dumps({"channel": "HostChannel"}),
                "data": json.dumps({"action": "ping"})
            }
            await websocket.send(json.dumps(ping_message))
            response = await websocket.recv()
            print(f"Received: {response}")

            if json.loads(response).get("type") == "pong":
                print("Ping test succeeded.")
                return websocket
    except Exception as e:
        print(f"Connection failed: {e}")
    return None

async def process_task(task):
    print(f"Processing task: {task}")
    proc = await asyncio.create_subprocess_exec(
        'bash',
        '-c',
        task,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    if stdout:
        print(stdout.decode())
    if stderr:
        print('\n\n == STDERR ==\n' + stderr.decode())
    sys.stdout.flush()
    sys.stderr.flush()

async def task_listener(auth_type):
    websocket = await connect_and_subscribe(auth_type)
    if not websocket:
        print("Exiting due to unsuccessful WebSocket connection.")
        return

    print('\nVM is ready to accept tasks. :)\n')
    sys.stdout.flush()

    while True:
        try:
            task = await websocket.recv()
            print('Got task: ' + task)
            task = json.loads(task)
            await process_task(task['command'])
        except websockets.ConnectionClosed:
            print("Connection closed, reconnecting...")
            await asyncio.sleep(1)
            websocket = await connect_and_subscribe(auth_type)
            if not websocket:
                print("Exiting due to unsuccessful WebSocket reconnection.")
                return
        except Exception as e:
            print(f"Error processing task: {e}")

async def main(auth_type):
    await task_listener(auth_type)

if __name__ == "__main__":
    auth_type = "host"  # or "user" based on your context
    asyncio.get_event_loop().run_until_complete(main(auth_type))
