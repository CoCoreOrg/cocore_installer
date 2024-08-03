import os
import json
import argparse
import asyncio
import websockets
import subprocess
import time

FIRECRACKER_BIN = "/usr/local/bin/firecracker"
FIRECRACKER_SOCKET = "/tmp/firecracker.socket"
WEBSOCKET_SERVER = "ws://localhost:8765"
FIRECRACKER_CONFIG_PATH = '/root/cocore_installer/cocore_installer/firecracker_config.json'

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

def send_firecracker_request(endpoint, data):
    cmd = [
        'curl',
        '-X', 'PUT',
        '--unix-socket', FIRECRACKER_SOCKET,
        '-H', 'Content-Type: application/json',
        '-d', json.dumps(data),
        f'http://localhost/{endpoint}'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(f'Endpoint: {endpoint}, Status: {result.returncode}, Response: {result.stdout.strip()}')

def start_firecracker_with_config(cpu_count, ram_size):
    # Start Firecracker
    firecracker_process = subprocess.Popen([FIRECRACKER_BIN, '--api-sock', FIRECRACKER_SOCKET])

    # Wait a bit for Firecracker to start
    time.sleep(1)

    # Load VM configuration
    with open(FIRECRACKER_CONFIG_PATH) as f:
        vm_config = json.load(f)

    # Update VM configuration with CPU and RAM limits
    vm_config["machine-config"]["vcpu_count"] = cpu_count
    vm_config["machine-config"]["mem_size_mib"] = ram_size

    # Ensure each drive has a unique ID
    for drive in vm_config.get("drives", []):
        if drive.get("drive_id") is None:
            drive["drive_id"] = "rootfs"  # Default to "rootfs" if no ID is provided

    # Ensure each network interface has a unique ID
    for i, iface in enumerate(vm_config.get("network-interfaces", [])):
        if iface.get("iface_id") is None:
            iface["iface_id"] = f"eth{i}"

    # Configure the VM
    for endpoint, data in vm_config.items():
        if data is not None:  # Only send non-null data
            send_firecracker_request(endpoint, data)

    # Start the VM
    send_firecracker_request('actions', {"action_type": "InstanceStart"})

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
