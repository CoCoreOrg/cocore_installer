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
    subprocess.run(['pkill', '-f', FIRECRACKER_BIN])
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
    firecracker_process = subprocess.Popen([FIRECRACKER_BIN, '--api-sock', FIRECRACKER_SOCKET])
    time.sleep(1)

    with open(FIRECRACKER_CONFIG_PATH) as f:
        vm_config = json.load(f)

    vm_config["machine-config"]["vcpu_count"] = cpu_count
    vm_config["machine-config"]["mem_size_mib"] = ram_size

    for drive in vm_config.get("drives", []):
        if not drive.get("drive_id"):
            drive["drive_id"] = "rootfs"  # Default to "rootfs" if no ID is provided

    for i, iface in enumerate(vm_config.get("network-interfaces", [])):
        if not iface.get("iface_id"):
            iface["iface_id"] = f"eth{i}"

    # Configure the VM
    send_firecracker_request('boot-source', vm_config["boot-source"])
    send_firecracker_request('drives/rootfs', {
        "drive_id": "rootfs",
        "path_on_host": "ubuntu-22.04.ext4",
        "is_root_device": True,
        "is_read_only": False,
    })
    # for drive in vm_config.get("drives", []):
    #     send_firecracker_request('drives', drive)
    send_firecracker_request('machine-config', vm_config["machine-config"])

    # Ensure each network interface has a unique ID
    for iface in vm_config.get("network-interfaces", []):
        send_firecracker_request('network-interfaces', iface)

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
        print("Checking WebSocket server...")
        time.sleep(5)
        asyncio.get_event_loop().run_until_complete(register_machine())

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        asyncio.get_event_loop().run_until_complete(deregister_machine())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cleanup_existing_firecracker_processes()

if __name__ == "__main__":
    main()