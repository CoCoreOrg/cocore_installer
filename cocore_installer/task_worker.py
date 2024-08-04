import time
import json
import requests
import asyncio
import websockets
from cryptography.fernet import Fernet
import sys

AUTH_KEY_FILE = "/etc/cocore/auth_key"
SECRET_KEY_FILE = "/etc/cocore/secret.key"
WEBSOCKET_SERVER = "ws://161.35.61.125:3001/vm"

def load_auth_key():
    with open(SECRET_KEY_FILE, "rb") as key_file:
        key = key_file.read()

    cipher_suite = Fernet(key)
    
    with open(AUTH_KEY_FILE, "rb") as file:
        encrypted_key = file.read()

    return cipher_suite.decrypt(encrypted_key).decode()

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
        print(stdout)
    if stderr:
        print('\n\n == STDERR ==\n' + stderr)
    sys.stdout.flush()
    sys.stderr.flush()

async def task_listener():
    async with websockets.connect(WEBSOCKET_SERVER) as websocket:

        print('\nVM is ready to accept tasks. :)\n')
        sys.stdout.flush()

        while True:
            task = await websocket.recv()
            print('Got task: ' + task)
            task = json.loads(task)
            await process_task(task['command'])

def main():
    auth_key = load_auth_key()
    asyncio.get_event_loop().run_until_complete(task_listener())

if __name__ == "__main__":
    main()
