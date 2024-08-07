#!/bin/bash

set -e

SCRIPT_DIR=$(cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd)

VM_NUMBER="$1"

if [ -z "${VM_NUMBER}" ] || [ "${VM_NUMBER}" -lt 1 ] || [ "${VM_NUMBER}" -gt 254 ]; then
	echo "Usage: $0 <vm_number>"
	echo "  where <vm_number> is a positive integer between 1 and 254"
	exit 1
fi

# TODO: Generate a better random name (since $RANDOM only generates four or five digit numbers)
RUN_ID="$(echo $RANDOM | shasum | cut -f 1 -d ' ')"

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

# Create a 1 GB ext4-formatted overlay
mkdir -p "${PWD}/disks"
dd if=/dev/zero of="${OVERLAY_FILE}" conv=sparse bs=1M count=1024
mkfs.ext4 "${OVERLAY_FILE}"

# Mount the CoCore keys in the VM
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

umount -R "/mnt/${RUN_ID}"
rmdir "/mnt/${RUN_ID}"

# Configure the tapfcN network device on the host
"${SCRIPT_DIR}/configure_tap.sh" 'eth0' "${TAP_DEVICE}" "${GATEWAY_IP}/30"

# Shut down running VMs when the script exits
cleanup() {
	echo -e "\nEXIT - Cleaning up running VMs."

	pkill -f "${FIRECRACKER_BIN}"

	# Remove the socket
	if [ -e "${FIRECRACKER_SOCKET}" ]; then
		rm "${FIRECRACKER_SOCKET}"
	fi
}
trap cleanup EXIT

# Start the Firecracker service
mkdir -p `dirname "${FIRECRACKER_SOCKET}"`
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
	--config-file "${PWD}/config/${RUN_ID}.json"
	# 2>&1 >> "${PWD}/firecracker.log" &

