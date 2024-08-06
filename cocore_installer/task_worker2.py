import time
import json
import asyncio
import websockets
import ssl
import sys
from cryptography.fernet import Fernet

AUTH_KEY_FILE = "/etc/cocore/auth_key"
SECRET_KEY_FILE = "/etc/cocore/secret.key"
WEBSOCKET_SERVER = "wss://cocore.io:80/vm"
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

async def ping_test():
    ssl_context = ssl.create_default_context()
    ssl_context.load_cert_chain(certfile=CLIENT_CERT_FILE, keyfile=CLIENT_KEY_FILE)
    ssl_context.load_verify_locations(cafile=CA_CERT_FILE)
    ssl_context.verify_mode = ssl.CERT_REQUIRED

    try:
        async with websockets.connect(WEBSOCKET_SERVER, ssl=ssl_context) as websocket:
            print("Connected to WebSocket server")
            await websocket.send(json.dumps({"type": "ping"}))
            response = await websocket.recv()
            print(f"Received: {response}")
            if json.loads(response).get("type") == "pong":
                return True
    except Exception as e:
        print(f"Connection failed: {e}")
    return False

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

async def task_listener():
    ssl_context = ssl.create_default_context()
    ssl_context.load_cert_chain(certfile=CLIENT_CERT_FILE, keyfile=CLIENT_KEY_FILE)
    ssl_context.load_verify_locations(cafile=CA_CERT_FILE)
    ssl_context.verify_mode = ssl.CERT_REQUIRED

    async with websockets.connect(WEBSOCKET_SERVER, ssl=ssl_context) as websocket:
        print('\nVM is ready to accept tasks. :)\n')
        sys.stdout.flush()

        while True:
            task = await websocket.recv()
            print('Got task: ' + task)
            task = json.loads(task)
            await process_task(task['command'])

async def main():
    auth_key = load_auth_key()
    ping_successful = await ping_test()
    if ping_successful:
        await task_listener()
    else:
        print("Ping test failed. Exiting.")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
