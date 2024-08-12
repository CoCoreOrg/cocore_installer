#!/bin/bash

set -e

SCRIPT_DIR=$(cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd)
LOGFILE="/var/log/start_vm.log"

log() {
    echo "$(date +'%Y-%m-%d %H:%M:%S') - $1" | tee -a "${LOGFILE}"
}

log "Script started."

VM_NUMBER="$1"

if [ -z "${VM_NUMBER}" ] || [ "${VM_NUMBER}" -lt 1 ] || [ "${VM_NUMBER}" -gt 254 ]; then
    log "Invalid VM number: ${VM_NUMBER}. Must be between 1 and 254."
    echo "Usage: $0 <vm_number>"
    echo "  where <vm_number> is a positive integer between 1 and 254"
    exit 1
fi

log "VM number is valid: ${VM_NUMBER}"

# Unique identifier for this VM instance
RUN_ID="vm${VM_NUMBER}"

SQUASHFS_FILE="/firecracker/cocore/squashfs.img"
KERNEL_FILE="/firecracker/cocore/vmlinux"
OVERLAY_FILE="${PWD}/disks/${RUN_ID}.ext4"

FIRECRACKER_BIN='/usr/local/bin/firecracker'
FIRECRACKER_SOCKET="/firecracker/sockets/${RUN_ID}.socket"

TAP_DEVICE="tapfc${VM_NUMBER}"
# Compute the guest's MAC address and IP from the VM number.
GATEWAY_IP="172.16.${VM_NUMBER}.1"
GUEST_IP="172.16.${VM_NUMBER}.2"
GUEST_MAC="06:00:AC:10:$(printf '%02x' ${VM_NUMBER}):02"

log "Stopping any existing VM with RUN_ID=${RUN_ID}..."
FIRECRACKER_PID=$(pgrep -f "${FIRECRACKER_BIN}")

log "FIRECRACKER_PID value: ${FIRECRACKER_PID}"

if [ -n "${FIRECRACKER_PID}" ]; then
    log "Found Firecracker process with PID=${FIRECRACKER_PID}. Attempting to stop..."
    if kill "${FIRECRACKER_PID}"; then
        log "Successfully sent kill signal to PID=${FIRECRACKER_PID}."
    else
        log "Failed to send kill signal to PID=${FIRECRACKER_PID}."
        exit 1
    fi

    log "Waiting for Firecracker process to terminate..."
    if wait "${FIRECRACKER_PID}" 2>/dev/null; then
        log "Firecracker process terminated successfully."
    else
        log "Firecracker process did not terminate cleanly."
        exit 1
    fi
else
    log "No existing Firecracker process found with RUN_ID=${RUN_ID}."
fi

# Remove any existing socket and overlay file
if [ -e "${FIRECRACKER_SOCKET}" ]; then
    log "Removing existing Firecracker socket: ${FIRECRACKER_SOCKET}"
    rm "${FIRECRACKER_SOCKET}"
fi

if [ -e "${OVERLAY_FILE}" ]; then
    log "Removing existing overlay file: ${OVERLAY_FILE}"
    rm "${OVERLAY_FILE}"
fi

# Create a new 4 GB ext4-formatted overlay
log "Creating a new 4 GB overlay filesystem: ${OVERLAY_FILE}"
mkdir -p "${PWD}/disks"
dd if=/dev/zero of="${OVERLAY_FILE}" conv=sparse bs=1M count=4096
mkfs.ext4 "${OVERLAY_FILE}"
log "Overlay filesystem created successfully."

# Mount the CoCore keys in the VM
log "Mounting overlay filesystem at /mnt/${RUN_ID}"
mkdir -p "/mnt/${RUN_ID}"
mount -o loop "${OVERLAY_FILE}" "/mnt/${RUN_ID}"

mkdir -p "/mnt/${RUN_ID}/root/etc"
cp -r /etc/cocore "/mnt/${RUN_ID}/root/etc"

mkdir -p "/mnt/${RUN_ID}/root/root"
cp "${SCRIPT_DIR}/init.sh" "/mnt/${RUN_ID}/root/root/init.sh"
cp "${SCRIPT_DIR}/task_worker.py" "/mnt/${RUN_ID}/root/root/task_worker.py"
chmod +x "/mnt/${RUN_ID}/root/root/init.sh"

mkdir -p "/mnt/${RUN_ID}/root/etc/systemd/system"
cp "${SCRIPT_DIR}/cocore.service" "/mnt/${RUN_ID}/root/etc/systemd/system/cocore.service"
systemctl --root="/mnt/${RUN_ID}/root" enable cocore.service

log "Setting up swapfile."
SWAP_FILE="/mnt/${RUN_ID}/root/swapfile"
dd if=/dev/zero of="${SWAP_FILE}" bs=1M count=1024
chmod 600 "${SWAP_FILE}"
mkswap "${SWAP_FILE}"
log "Swapfile setup complete."

umount -R "/mnt/${RUN_ID}"
rmdir "/mnt/${RUN_ID}"
log "Unmounted overlay filesystem."

# Configure the tapfcN network device on the host
log "Configuring network device: ${TAP_DEVICE}"
"${SCRIPT_DIR}/configure_tap.sh" 'eth0' "${TAP_DEVICE}" "${GATEWAY_IP}/30"
log "Network device configured."

# Start the Firecracker service
log "Starting Firecracker service..."
mkdir -p "$(dirname "${FIRECRACKER_SOCKET}")"
mkdir -p "${PWD}/config"
cat > "${PWD}/config/${RUN_ID}.json" <<-EOF
    {
        "boot-source": {
            "kernel_image_path": "${KERNEL_FILE}",
            "boot_args": "console=ttyS0 reboot=k panic=1 pci=off overlay_root=vdb init=/sbin/overlay-init ip=${GUEST_IP}:::255.255.255.252::eth0:off"
        },
        "drives": [
            {
                "drive_id": "rootfs",
                "path_on_host": "${SQUASHFS_FILE}",
                "is_root_device": true,
                "is_read_only": true
            },
            {
                "drive_id": "overlayfs",
                "path_on_host": "${OVERLAY_FILE}",
                "is_root_device": false
            }
        ],
        "machine-config": {
            "vcpu_count": 2,
            "mem_size_mib": 1024,
            "smt": false
        },
        "network-interfaces": [
            {
                "iface_id": "net1",
                "guest_mac": "${GUEST_MAC}",
                "host_dev_name": "${TAP_DEVICE}"
            }
        ]
    }
EOF

"${FIRECRACKER_BIN}" \
    --api-sock "${FIRECRACKER_SOCKET}" \
    --config-file "${PWD}/config/${RUN_ID}.json" \
    2>&1 | tee -a "${LOGFILE}" &

log "Firecracker VM started successfully with RUN_ID=${RUN_ID}."
