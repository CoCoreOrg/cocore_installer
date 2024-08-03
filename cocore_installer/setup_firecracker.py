import os
import json
import argparse
import asyncio
import websockets
import subprocess
import time

FIRECTL_BIN = "/usr/local/bin/firectl"
FIRECRACKER_CONFIG_PATH = 'cocore_installer/firecracker_config.json'
KERNEL_PATH = "vmlinux"
ROOTFS_PATH = "rootfs.ext4"
WEBSOCKET_SERVER = "ws://localhost:8765"

async def register_machine():
    async with websockets.connect(WEBSOCKET_SERVER) as websocket:
        await websocket.send(json.dumps({"action": "register"}))

async def deregister_machine():
    async with websockets.connect(WEBSOCKET_SERVER) as websocket:
        await websocket.send(json.dumps({"action": "deregister"}))

def start_firecracker_with_firectl(cpu_count, ram_size):
    cmd = [
        FIRECTL_BIN,
        '--firecracker-binary', '/usr/local/bin/firecracker',
        '--kernel', KERNEL_PATH,
        '--root-drive', ROOTFS_PATH,
        '--ncpus', str(cpu_count),
        '--memory', str(ram_size)
    ]
    subprocess.Popen(cmd)

def main():
    parser = argparse.ArgumentParser(description="Configure and start a Firecracker microVM.")
    parser.add_argument('--cpu', type=int, default=2, help='Number of vCPUs for the microVM')
    parser.add_argument('--ram', type=int, default=1024, help='Memory size in MiB for the microVM')
    args = parser.parse_args()

    try:
        start_firecracker_with_firectl(args.cpu, args.ram)

        # Check if the WebSocket server is running
        print("Checking WebSocket server...")
        time.sleep(5)  # Give it some time to start
        asyncio.get_event_loop().run_until_complete(register_machine())
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        asyncio.get_event_loop().run_until_complete(deregister_machine())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        subprocess.run(['pkill', '-f', FIRECTL_BIN])

if __name__ == "__main__":
    main()
