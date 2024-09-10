import os
import subprocess
import psutil
import sys
import asyncio
import json
import ssl
import requests
import tempfile
import time
import traceback
import redis
import signal
from cryptography.fernet import Fernet
from concurrent.futures import ThreadPoolExecutor, as_completed
from task_runners import TaskRunners
from task_extensions import TaskExtensions
MAX_THREADS = 10
LANGUAGE_MAP = {
    "1": "python",
    "2": "node",
    "3": "ruby",
    "4": "go",
    "5": "rust",
    "6": "java",
}
AUTH_KEY_FILE = "/etc/cocore/auth_key"
SECRET_KEY_FILE = "/etc/cocore/secret.key"
CERT_DIR = "/etc/cocore/certificates"
CLIENT_CERT_FILE = f"{CERT_DIR}/client.crt"
CLIENT_KEY_FILE = f"{CERT_DIR}/client.key"
CA_CERT_FILE = f"{CERT_DIR}/ca.crt"
MAX_THREADS = psutil.cpu_count(logical=True)
CPU_THRESHOLD = 80.0  # CPU usage threshold in percentage
def connect_to_redis():
    auth_key = load_auth_key()
    redis_url = os.getenv('REDIS_SERVER', 'redis://scheduler.cocore.io:6379/0')
    client = redis.Redis.from_url(redis_url, username=auth_key, password=auth_key)
    return client, f'job_queue:{auth_key}'

def monitor_cpu_usage():
    return psutil.cpu_percent(interval=1)

def should_launch_more_threads():
    current_cpu_usage = monitor_cpu_usage()
    print(f"Current CPU usage: {current_cpu_usage}%")
    return current_cpu_usage < CPU_THRESHOLD

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

def send_specs(auth_key, cpu, ram):
    payload = {
        "cpu": cpu,
        "ram": ram
    }

    headers = {
        "Authorization": f"Bearer {auth_key}",
        "Content-Type": "application/json"
    }

    cmd = [
        'curl',
        '-X', 'POST',
        '-H', f'Authorization: Bearer {auth_key}',
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

def fetch_task_execution(execution_id):
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

def run_task(task_language_id, task_requirements, task_code, input_args):
    task_language = LANGUAGE_MAP.get(str(task_language_id))
    if "python" in task_language:
        return TaskRunners.run_python_task(task_requirements, task_code, input_args, TaskExtensions.python_extension(input_args))
    elif "node" in task_language:
        return TaskRunners.run_node_task(task_requirements, task_code, input_args, TaskExtensions.node_extension(input_args))
    elif "ruby" in task_language:
        return TaskRunners.run_ruby_task(task_requirements, task_code, input_args, TaskExtensions.ruby_extension(input_args))
    elif "go" in task_language:
        return TaskRunners.run_go_task(task_requirements, task_code, input_args, TaskExtensions.go_extension(input_args))
    elif "rust" in task_language:
        return TaskRunners.run_rust_task(task_requirements, task_code, input_args, TaskExtensions.rust_extension(input_args))
    elif "java" in task_language:
        return TaskRunners.run_java_task(task_requirements, task_code, input_args, TaskExtensions.java_extension(input_args))
    else:
        return {"error": "UnsupportedLanguage", "error_message": f"Language '{task_language}' is not supported."}

async def process_task_execution_concurrently(execution_id, executor):
    executor.submit(process_task_execution, execution_id)
    return future.result()

async def process_all_pending_tasks_concurrently():
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        tasks = []
        while True:
            task_execution = await fetch_next_task_execution()
            if task_execution is None:
                print("No more pending task executions found.")
                break

            execution_id = task_execution['id']

            if should_launch_more_threads():
                # Start a new asyncio task to process the execution concurrently
                task = asyncio.create_task(process_task_execution_concurrently(execution_id, executor))
                tasks.append(task)

            await asyncio.sleep(1)  # Add delay to avoid spamming the server

        # Await all tasks to ensure they complete
        for task in tasks:
            await task

async def set_host_status(status):
    set_host_status_sync(status)

def set_host_status_sync(status):
    try:
        url = f"https://cocore.io/set_host_status"
        headers = {
            "Authorization": f"Bearer {load_auth_key()}",
            "Content-Type": "application/json"
        }
        payload = {
            "status": status
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print(f"Host status set to {status} successfully")
        else:
            print(f"Failed to set host status to {status}: {response.status_code}")
    except Exception as e:
        print(f"Error setting host status to {status}: {e}")
        print(traceback.format_exc())

def process_task_execution_by_task_execution(task_execution):
    try:
        execution_id = task_execution["id"]
        task_language = task_execution['task']['language']
        task_code = task_execution['task']['code']
        task_requirements = task_execution['task']['requirements']
        input_args = task_execution['input'] or []
        result = run_task(task_language, task_requirements, task_code, input_args)
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

def process_task_execution(execution_id):
    try:
        task_execution = fetch_task_execution(execution_id)
        task_language = task_execution['task']['language']
        task_code = task_execution['task']['code']
        task_requirements = task_execution['task']['requirements']
        input_args = task_execution['input'] or []
        result = run_task(task_language, task_requirements, task_code, input_args)

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

def task_listener():
    redis_client, queue_name = connect_to_redis()
    
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = []
        
        while True:
            if should_launch_more_threads():
                # Use BLPOP to block until a task is available
                _, task_execution_raw = redis_client.blpop(queue_name, timeout=0)
                if task_execution_raw:
                    task_execution = json.loads(task_execution_raw)
                    future = executor.submit(process_task_execution_by_task_execution, task_execution)
                    futures.append(future)
                else:
                    print("No task found in the queue.")
            # Clean up completed futures
            futures = [f for f in futures if not f.done()]
            time.sleep(1)  # Avoid spamming Redis with requests

def shutdown_handler(signal_received, frame):
    """Handle shutdown signals and set host status to offline."""
    print(f"Received exit signal {signal_received}...")
    set_host_status("offline")
    sys.exit(0)

async def main():
    total_cpus, total_memory = get_system_resources()
    set_host_status_sync("online")
    auth_key = load_auth_key()
    send_specs(auth_key, total_cpus, total_memory)

    try:
        await process_all_pending_tasks_concurrently()  # Process all pending tasks concurrently
        task_listener()  # Start listening for new tasks
    except Exception as e:
        print(f"Exception occurred in main loop: {e}")
        print(traceback.format_exc())
    finally:
        await set_host_status("offline")

if __name__ == "__main__":
    # Register signal handlers for a clean shutdown
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    set_host_status_sync("online")

    try:
        asyncio.run(main())  # Run the main event loop
    finally:
        set_host_status_sync("offline")