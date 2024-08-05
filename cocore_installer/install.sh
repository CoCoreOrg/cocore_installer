#!/bin/bash

set -e

# Variables
FIRECRACKER_VERSION="1.8.0"
ROOTFS_FILE="ubuntu-22.04.ext4"
KERNEL_FILE="vmlinux"
SSH_KEY_FILE="firecracker.rsa"
ARCH=$(uname -m)
MOUNT_POINT="mnt"
TASK_WORKER_SCRIPT="cocore_installer/task_worker.py"
API_SOCKET="/tmp/firecracker.socket"
LOGFILE="./cocore_installer/firecracker.log"
COCORE_DIR="/etc/cocore"

# Prerequisites
echo "Checking KVM module..."
if ! lsmod | grep -q kvm; then
    echo "KVM module is not loaded. Please load the KVM module."
    exit 1
fi

echo "Checking access to /dev/kvm..."
if [ ! -r /dev/kvm ] || [ ! -w /dev/kvm ]; then
    echo "Access to /dev/kvm is required. Granting access..."
    sudo setfacl -m u:${USER}:rw /dev/kvm || (sudo usermod -aG kvm ${USER} && echo "Access granted. Please re-login for the group changes to take effect." && exit 1)
fi

# Download Firecracker and Jailer
install_dir="/firecracker/releases"
bin_dir="/usr/local/bin"
release_url="https://github.com/firecracker-microvm/firecracker/releases/download/v${FIRECRACKER_VERSION}"

mkdir -p "${install_dir}/release-v${FIRECRACKER_VERSION}"
download_url="${release_url}/firecracker-v${FIRECRACKER_VERSION}-${ARCH}.tgz"
echo "Attempting to download Firecracker from URL: ${download_url}"
wget -O "${install_dir}/firecracker-v${FIRECRACKER_VERSION}-${ARCH}.tgz" "${download_url}"

echo "Decompressing firecracker-v${FIRECRACKER_VERSION}-${ARCH}.tgz in ${install_dir}/release-v${FIRECRACKER_VERSION}"
tar -xzf "${install_dir}/firecracker-v${FIRECRACKER_VERSION}-${ARCH}.tgz" -C "${install_dir}/release-v${FIRECRACKER_VERSION}"
rm "${install_dir}/firecracker-v${FIRECRACKER_VERSION}-${ARCH}.tgz"

echo "Contents of ${install_dir}/release-v${FIRECRACKER_VERSION}:"
ls -l "${install_dir}/release-v${FIRECRACKER_VERSION}"

# Handle nested directory structure
nested_dir="${install_dir}/release-v${FIRECRACKER_VERSION}/release-v${FIRECRACKER_VERSION}-${ARCH}"

echo "Linking firecracker and jailer"
if [ -f "${nested_dir}/firecracker-v${FIRECRACKER_VERSION}-${ARCH}" ]; then
    sudo ln -sfn "${nested_dir}/firecracker-v${FIRECRACKER_VERSION}-${ARCH}" "${bin_dir}/firecracker"
else
    echo "Firecracker binary not found in ${nested_dir}"
    exit 1
fi

if [ -f "${nested_dir}/jailer-v${FIRECRACKER_VERSION}-${ARCH}" ]; then
    sudo ln -sfn "${nested_dir}/jailer-v${FIRECRACKER_VERSION}-${ARCH}" "${bin_dir}/jailer"
else
    echo "Jailer binary not found in ${nested_dir}"
    exit 1
fi

echo "firecracker and jailer ${FIRECRACKER_VERSION}-${ARCH}: ready"
ls -l "${bin_dir}/firecracker"
file "${bin_dir}/firecracker"
file "${bin_dir}/jailer"
"${bin_dir}/firecracker" --version | head -n1

# Download Kernel and Root Filesystem
echo "Downloading kernel and root filesystem..."
ARCH="$(uname -m)"

latest=$(wget "http://spec.ccfc.min.s3.amazonaws.com/?prefix=firecracker-ci/v1.9/x86_64/vmlinux-5.10&list-type=2" -O - 2>/dev/null | grep "(?<=<Key>)(firecracker-ci/v1.9/x86_64/vmlinux-5\.10\.[0-9]{3})(?=</Key>)" -o -P)

kernel_url="https://s3.amazonaws.com/spec.ccfc.min/${latest}"
rootfs_url="https://s3.amazonaws.com/spec.ccfc.min/firecracker-ci/v1.9/${ARCH}/ubuntu-22.04.ext4"
ssh_key_url="https://s3.amazonaws.com/spec.ccfc.min/firecracker-ci/v1.9/${ARCH}/ubuntu-22.04.id_rsa"

wget -O "${SSH_KEY_FILE}" "${ssh_key_url}" || { echo "Failed to download the SSH key"; exit 1; }
chmod 400 "${SSH_KEY_FILE}"

# Ensure the root filesystem is in place
if [ ! -f "${ROOTFS_FILE}" ]; then
    echo "Root filesystem not found. Downloading..."
    wget -O "${ROOTFS_FILE}" "${rootfs_url}" || { echo "Failed to download root filesystem"; exit 1; }
fi

# Ensure the kernel is in place
if [ ! -f $KERNEL_FILE ]; then
    echo "Kernel image not found. Downloading..."
    wget -O "${KERNEL_FILE}" "${kernel_url}" || { echo "Failed to download kernel"; exit 1; }
fi

# Check if already mounted and unmount if necessary
if mountpoint -q $MOUNT_POINT; then
    echo "$MOUNT_POINT is already mounted. Unmounting..."
    sudo umount $MOUNT_POINT
fi

# Resize Ubuntu image to 4 GB
e2fsck -yf "${ROOTFS_FILE}"
resize2fs -f "${ROOTFS_FILE}" 1024000

# Copy task worker script to rootfs
mkdir -p $MOUNT_POINT
sudo mount -o loop $ROOTFS_FILE $MOUNT_POINT
sudo cp $TASK_WORKER_SCRIPT $MOUNT_POINT/root/task_worker.py

# Loop for auth key
while true; do
    echo "Please enter your authentication key:"
    read -s auth_key

    if python3 store_auth_key.py \
        --key "$auth_key" \
        --mount_point "${MOUNT_POINT}" \
        --cocore_directory "${COCORE_DIR}" \
        --keyfile "${COCORE_DIR}/auth_key" \
        --secretfile "${COCORE_DIR}/secret.key" \
        --workdir "$(pwd)"; then
        break
    else
        echo "Authentication failed. Please try again."
    fi
done

# Copy the init script to rootfs
sudo cp cocore_installer/init.sh $MOUNT_POINT/root/init.sh
sudo chmod +x "${MOUNT_POINT}/root/init.sh"

cat > "$MOUNT_POINT/etc/systemd/system/cocore.service" <<EOF
[Unit]
Description=CoCore Startup Service

[Service]
Type=simple
ExecStart=/root/init.sh

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl --root=$MOUNT_POINT enable cocore.service

sudo umount $MOUNT_POINT
rm -rf $MOUNT_POINT

echo "Setup complete. Use 'cocore-setup-firecracker' to configure and start Firecracker."
