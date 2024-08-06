import asyncio
import websockets
import json

WEBSOCKET_SERVER = "ws://cocore.io/cable"  # Insecure WebSocket URL

async def test_websocket():
    async with websockets.connect(WEBSOCKET_SERVER) as websocket:
        await websocket.send(json.dumps({"type": "ping"}))
        response = await websocket.recv()
        print(f"Received: {response}")

async def main():
    try:
        await test_websocket()
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
