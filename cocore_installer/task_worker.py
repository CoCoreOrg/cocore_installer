import time
import json
import requests
import asyncio
import websockets
from cryptography.fernet import Fernet

AUTH_KEY_FILE = "/etc/cocore/auth_key"
SECRET_KEY_FILE = "/etc/cocore/secret.key"
WEBSOCKET_SERVER = "ws://localhost:8765"

def load_auth_key():
    with open(SECRET_KEY_FILE, "rb") as key_file:
        key = key_file.read()

    cipher_suite = Fernet(key)
    
    with open(AUTH_KEY_FILE, "rb") as file:
        encrypted_key = file.read()

    return cipher_suite.decrypt(encrypted_key).decode()

async def process_task(task):
    print(f"Processing task: {task}")
    await asyncio.sleep(task.get('duration', 1))

async def task_listener():
    async with websockets.connect(WEBSOCKET_SERVER) as websocket:
        while True:
            task = await websocket.recv()
            task = json.loads(task)
            await process_task(task)

def main():
    auth_key = load_auth_key()
    asyncio.get_event_loop().run_until_complete(task_listener())

if __name__ == "__main__":
    main()
