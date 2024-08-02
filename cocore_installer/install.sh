#!/bin/bash

set -e

# Variables
FIRECRACKER_VERSION="1.8.0"
ROOTFS_FILE="ubuntu-22.04.ext4"
KERNEL_FILE="vmlinux-5.10"
ARCH=$(uname -m)
MOUNT_POINT="mnt"
TASK_WORKER_SCRIPT="cocore_installer/task_worker.py"  # Correct path to task_worker.py
API_SOCKET="/tmp/firecracker.socket"
LOGFILE="./firecracker.log"

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
kernel_url="https://s3.amazonaws.com/spec.ccfc.min/firecracker-ci/v1.9/${ARCH}/${KERNEL_FILE}"
rootfs_url="https://s3.amazonaws.com/spec.ccfc.min/firecracker-ci/v1.9/${ARCH}/${ROOTFS_FILE}"
ssh_key_url="https://s3.amazonaws.com/spec.ccfc.min/firecracker-ci/v1.9/${ARCH}/ubuntu-22.04.id_rsa"

wget -O "${KERNEL_FILE}" "${kernel_url}" || { echo "Failed to download kernel"; exit 1; }
wget -O "${ROOTFS_FILE}" "${rootfs_url}" || { echo "Failed to download root filesystem"; exit 1; }
wget -O "ubuntu-22.04.id_rsa" "${ssh_key_url}" || { echo "Failed to download SSH key"; exit 1; }
chmod 400 "ubuntu-22.04.id_rsa"

# Ensure the root filesystem is in place
if [ ! -f $ROOTFS_FILE ]; then
    echo "Root filesystem not found. Downloading..."
    wget $rootfs_url -O rootfs.ext4
fi

# Ensure the kernel is in place
if [ ! -f $KERNEL_FILE ]; then
    echo "Kernel image not found. Downloading..."
    wget $kernel_url -O vmlinux
fi

# Check if already mounted and unmount if necessary
if mountpoint -q $MOUNT_POINT; then
    echo "$MOUNT_POINT is already mounted. Unmounting..."
    sudo umount $MOUNT_POINT
fi

# Copy task worker script to rootfs
mkdir -p $MOUNT_POINT
sudo mount -o loop $ROOTFS_FILE $MOUNT_POINT
sudo cp $TASK_WORKER_SCRIPT $MOUNT_POINT/root/task_worker.py
echo -e '#!/bin/sh\npython3 /root/task_worker.py' | sudo tee $MOUNT_POINT/root/init.sh
sudo chmod +x $MOUNT_POINT/root/init.sh
sudo umount $MOUNT_POINT
rm -rf $MOUNT_POINT

# Prompt for auth key
echo "Please enter your authentication key:"
read -s auth_key
cocore-store-auth-key --key "$auth_key"

echo "Setup complete. Use 'cocore-setup-firecracker' to configure and start Firecracker."
