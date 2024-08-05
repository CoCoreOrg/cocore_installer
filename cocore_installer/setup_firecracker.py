import os
import json
import argparse
import subprocess
import time
import psutil

FIRECRACKER_BIN = "/usr/local/bin/firecracker"
FIRECRACKER_SOCKET = "/tmp/firecracker.socket"
TAP_DEVICE = "tap0"
TAP_IP = "172.16.0.1"
TOKEN_PATH = "/etc/cocore/tokenfile"
FIRECRACKER_DEFAULT_CONFIG = {
  "boot-source": {
    "kernel_image_path": "vmlinux",
    "boot_args": "console=ttyS0 reboot=k panic=1 pci=off"
  },
  "drives": [
    {
      "drive_id": "rootfs",
      "path_on_host": "ubuntu-22.04.ext4",
      "is_root_device": True,
      "is_read_only": False,
      "cache_type": "Unsafe",
      "io_engine": "Sync"
    }
  ],
  "machine-config": {
    "vcpu_count": 2,
    "mem_size_mib": 1024,
    "smt": False
  },
  "network-interfaces": []
}

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
    #print(result)

def setup_host_network_devices():
    subprocess.run(["./setup-network.sh"])

def start_firecracker_with_config(cpu_count, ram_size):
    firecracker_process = subprocess.Popen([FIRECRACKER_BIN, '--api-sock', FIRECRACKER_SOCKET])
    time.sleep(1)

    vm_config = FIRECRACKER_DEFAULT_CONFIG

    vm_config["machine-config"]["vcpu_count"] = cpu_count
    vm_config["machine-config"]["mem_size_mib"] = ram_size

    for drive in vm_config.get("drives", []):
        if not drive.get("drive_id"):
            drive["drive_id"] = "rootfs"  # Default to "rootfs" if no ID is provided

    for i, iface in enumerate(vm_config.get("network-interfaces", [])):
        if not iface.get("iface_id"):
            iface["iface_id"] = f"eth{i}"

    send_firecracker_request('boot-source', vm_config["boot-source"])
    for drive in vm_config.get("drives", []):
        send_firecracker_request(f'drives/{drive["drive_id"]}', drive)
    send_firecracker_request('machine-config', vm_config["machine-config"])

    send_firecracker_request('network-interfaces/net1', {
        "iface_id": "net1",
        "guest_mac": "06:00:AC:10:00:02",
        "host_dev_name": TAP_DEVICE,
    })

    time.sleep(1)
    send_firecracker_request('actions', {"action_type": "InstanceStart"})

def send_specs(token, cpu, ram):
    payload = {
        "token": token,
        "cpu": cpu,
        "ram": ram
    }

    cmd = [
        'curl',
        '-X', 'POST',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps(payload),
        'https://cocore.io/hosts/update_specs'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    response = json.loads(result.stdout)

    if result.returncode == 0 and response.get("success"):
        print("Specifications updated successfully.")
    else:
        print(response.get("message"))

def get_system_resources():
    total_cpus = psutil.cpu_count(logical=True)
    total_memory = psutil.virtual_memory().total // (1024 * 1024)  # Convert bytes to MiB
    return total_cpus, total_memory

def main():
    total_cpus, total_memory = get_system_resources()

    parser = argparse.ArgumentParser(description="Configure and start a Firecracker microVM.")
    parser.add_argument('--cpu', type=int, default=total_cpus, help='Number of vCPUs for the microVM')
    parser.add_argument('--ram', type=int, default=total_memory, help='Memory size in MiB for the microVM')
    args = parser.parse_args()

    # Ensure the /etc/cocore directory exists
    os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)

    # Load the token
    with open(TOKEN_PATH, "r") as token_file:
        token = token_file.read().strip()

    send_specs(token, args.cpu, args.ram)

    cleanup_existing_firecracker_processes()

    try:
        start_firecracker_with_config(args.cpu, args.ram)
        print("Checking WebSocket server...")
        time.sleep(5)

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print('Cleaning up Firecracker processes')
        cleanup_existing_firecracker_processes()

if __name__ == "__main__":
    main()
