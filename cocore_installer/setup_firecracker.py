import os
import requests
import json
import argparse
import asyncio
import websockets
import subprocess
import time

FIRECRACKER_BIN = "/usr/local/bin/firecracker"
FIRECRACKER_SOCKET = "/tmp/firecracker.socket"
WEBSOCKET_SERVER = "ws://localhost:8765"

def configure_cgroup(cpu_quota):
    cgroup_name = "firecracker"
    cgroup_path = f"/sys/fs/cgroup/cpu/{cgroup_name}"

    # Create cgroup
    if not os.path.exists(cgroup_path):
        os.makedirs(cgroup_path)

    # Calculate CPU quota and period
    cpu_period = 100000  # Default period is 100000 microseconds
    cpu_quota_value = int(cpu_quota * cpu_period)

    # Set CPU quota and period with sudo
    subprocess.run(['sudo', 'sh', '-c', f'echo {cpu_period} > {os.path.join(cgroup_path, "cpu.cfs_period_us")}'], check=True)
    subprocess.run(['sudo', 'sh', '-c', f'echo {cpu_quota_value} > {os.path.join(cgroup_path, "cpu.cfs_quota_us")}'], check=True)

def add_pid_to_cgroup(pid):
    cgroup_name = "firecracker"
    cgroup_path = f"/sys/fs/cgroup/cpu/{cgroup_name}/tasks"

    # Add PID to cgroup tasks with sudo
    subprocess.run(['sudo', 'sh', '-c', f'echo {pid} > {cgroup_path}'], check=True)

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

    # Apply cgroup settings
    configure_cgroup(cpu_quota)
    add_pid_to_cgroup(firecracker_process.pid)

    # Load VM configuration
    with open(os.path.join(os.path.dirname(__file__), 'firecracker_config.json')) as f:
        vm_config = json.load(f)

    # Update VM configuration with CPU and RAM limits
    vm_config["machine-config"]["vcpu_count"] = cpu_count
    vm_config["machine-config"]["mem_size_mib"] = ram_size

    # Configure the VM
    for endpoint, data in vm_config.items():
        response = requests.put(f'http://localhost/{FIRECRACKER_SOCKET}/{endpoint}', json=data)
        print(response.status_code, response.text)

    # Start the VM
    response = requests.put(f'http://localhost/{FIRECRACKER_SOCKET}/actions', json={"action_type": "InstanceStart"})
    print(response.status_code, response.text)

def main():
    parser = argparse.ArgumentParser(description="Configure and start a Firecracker microVM.")
    parser.add_argument('--cpu', type=int, default=2, help='Number of vCPUs for the microVM')
    parser.add_argument('--ram', type=int, default=512, help='Memory size in MiB for the microVM')
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
