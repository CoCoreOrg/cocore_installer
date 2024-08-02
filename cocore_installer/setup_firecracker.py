import os
import json
import argparse
import asyncio
import websockets
import requests_unixsocket
import subprocess
import time

FIRECRACKER_BIN = "/usr/local/bin/firecracker"
FIRECRACKER_SOCKET = "/tmp/firecracker.socket"
WEBSOCKET_SERVER = "ws://localhost:8765"

async def register_machine():
    async with websockets.connect(WEBSOCKET_SERVER) as websocket:
        await websocket.send(json.dumps({"action": "register"}))

async def deregister_machine():
    async with websockets.connect(WEBSOCKET_SERVER) as websocket:
        await websocket.send(json.dumps({"action": "deregister"}))

def configure_firecracker(cpu_count, ram_size, cpu_quota):
    # Clean up any existing socket
    if os.path.exists(FIRECRACKER_SOCKET):
        os.remove(FIRECRACKER_SOCKET)

    # Start Firecracker
    firecracker_process = subprocess.Popen([FIRECRACKER_BIN, '--api-sock', FIRECRACKER_SOCKET])

    # Load VM configuration
    config_path = os.path.join(os.path.dirname(__file__), 'firecracker_config.json')
    with open(config_path) as f:
        vm_config = json.load(f)

    # Update VM configuration with CPU and RAM limits
    vm_config["machine-config"]["vcpu_count"] = cpu_count
    vm_config["machine-config"]["mem_size_mib"] = ram_size

    session = requests_unixsocket.Session()

    # Configure the VM
    for endpoint, data in vm_config.items():
        if data is not None:  # Only send non-null data
            response = session.put(f'http+unix://{FIRECRACKER_SOCKET.replace("/", "%2F")}/{endpoint}', json=data, headers={"Content-Type": "application/json"})
            print(f'Endpoint: {endpoint}, Status: {response.status_code}, Response: {response.text}')

    # Start the VM
    response = session.put(f'http+unix://{FIRECRACKER_SOCKET.replace("/", "%2F")}/actions', json={"action_type": "InstanceStart"}, headers={"Content-Type": "application/json"})
    print(f'Start VM, Status: {response.status_code}, Response: {response.text}')

def main():
    parser = argparse.ArgumentParser(description="Configure and start a Firecracker microVM.")
    parser.add_argument('--cpu', type=int, default=2, help='Number of vCPUs for the microVM')
    parser.add_argument('--ram', type=int, default=1024, help='Memory size in MiB for the microVM')
    parser.add_argument('--cpu-quota', type=float, default=1.0, help='CPU quota for the microVM (e.g., 0.5 for half a CPU)')
    args = parser.parse_args()

    configure_firecracker(args.cpu, args.ram, args.cpu_quota)

    try:
        asyncio.get_event_loop().run_until_complete(register_machine())
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        asyncio.get_event_loop().run_until_complete(deregister_machine())

if __name__ == "__main__":
    main()
