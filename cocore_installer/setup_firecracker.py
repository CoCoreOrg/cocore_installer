import os
import json
import argparse
import asyncio
import websockets
import subprocess
import time
import signal

FIRECRACKER_BIN = "/usr/local/bin/firecracker"
FIRECRACKER_SOCKET = "/tmp/firecracker.socket"
WEBSOCKET_SERVER = "ws://localhost:8765"

async def register_machine():
    async with websockets.connect(WEBSOCKET_SERVER) as websocket:
        await websocket.send(json.dumps({"action": "register"}))

async def deregister_machine():
    async with websockets.connect(WEBSOCKET_SERVER) as websocket:
        await websocket.send(json.dumps({"action": "deregister"}))

def cleanup_existing_firecracker_processes():
    # Kill all existing Firecracker processes
    subprocess.run(['pkill', '-f', FIRECRACKER_BIN])

    # Remove any existing socket
    if os.path.exists(FIRECRACKER_SOCKET):
        os.remove(FIRECRACKER_SOCKET)

def start_firecracker_with_config(cpu_count, ram_size):
    # Start Firecracker with the config file
    firecracker_process = subprocess.Popen([FIRECRACKER_BIN, '--api-sock', FIRECRACKER_SOCKET])

    # Load VM configuration
    config_path = os.path.join(os.path.dirname(__file__), 'firecracker_config.json')
    with open(config_path) as f:
        vm_config = json.load(f)

    # Update VM configuration with CPU and RAM limits
    vm_config["machine-config"]["vcpu_count"] = cpu_count
    vm_config["machine-config"]["mem_size_mib"] = ram_size

    # Save the updated configuration
    with open(config_path, 'w') as f:
        json.dump(vm_config, f, indent=4)

    # Start Firecracker with the config file
    subprocess.run([FIRECRACKER_BIN, '--config-file', config_path])

def main():
    parser = argparse.ArgumentParser(description="Configure and start a Firecracker microVM.")
    parser.add_argument('--cpu', type=int, default=2, help='Number of vCPUs for the microVM')
    parser.add_argument('--ram', type=int, default=1024, help='Memory size in MiB for the microVM')
    args = parser.parse_args()

    cleanup_existing_firecracker_processes()

    try:
        start_firecracker_with_config(args.cpu, args.ram)
        asyncio.get_event_loop().run_until_complete(register_machine())

        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        asyncio.get_event_loop().run_until_complete(deregister_machine())
    finally:
        cleanup_existing_firecracker_processes()

if __name__ == "__main__":
    main()
