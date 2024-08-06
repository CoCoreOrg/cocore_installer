import asyncio
import json
import ssl
import websockets
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
                    subscription_id = response_data.get("identifier")
                    break

            # Send the ping command after subscription confirmation
            ping_message = {
                "command": "message",
                "identifier": subscription_id,
                "data": json.dumps({"action": "ping"})
            }
            await websocket.send(json.dumps(ping_message))
            response = await websocket.recv()
            print(f"Received: {response}")

            if json.loads(response).get("type") == "pong":
                print("Ping test succeeded.")
                return websocket, subscription_id
    except Exception as e:
        print(f"Connection failed: {e}")
    return None, None

async def process_task(websocket, subscription_id, task):
    print(f"Processing task: {task}")
    try:
        # Send task processing command to the server
        task_message = {
            "command": "message",
            "identifier": subscription_id,
            "data": json.dumps({"action": "execute_task", "task": task})
        }
        await websocket.send(json.dumps(task_message))

        # Wait for the server's response
        response = await websocket.recv()
        print(f"Received: {response}")
    except Exception as e:
        print(f"Error processing task: {e}")

async def task_listener(auth_type):
    while True:
        websocket, subscription_id = await connect_and_subscribe(auth_type)
        if not websocket:
            print("Exiting due to unsuccessful WebSocket connection.")
            return

        print('\nVM is ready to accept tasks. :)\n')
        sys.stdout.flush()

        async with websocket:
            try:
                async for message in websocket:
                    print('Got message: ' + message)
                    task = json.loads(message)
                    await process_task(websocket, subscription_id, task['command'])
            except websockets.ConnectionClosed:
                print("Connection closed, reconnecting...")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Error processing task: {e}")

async def main(auth_type):
    await task_listener(auth_type)

if __name__ == "__main__":
    auth_type = "host"  # or "user" based on your context
    asyncio.run(main(auth_type))
