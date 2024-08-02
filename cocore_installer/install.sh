#!/bin/bash

set -e

# Variables
FIRECRACKER_VERSION="0.25.0"
ROOTFS_URL="https://dl-cdn.alpinelinux.org/alpine/latest-stable/releases/x86_64/alpine-minirootfs-3.17.0-x86_64.tar.gz"
KERNEL_URL="https://example.com/path/to/vmlinux"  # Replace with actual URL or local path

# Install Firecracker
curl -Lo firecracker https://github.com/firecracker-microvm/firecracker/releases/download/v${FIRECRACKER_VERSION}/firecracker-${FIRECRACKER_VERSION}
chmod +x firecracker
sudo mv firecracker /usr/local/bin/

# Create root filesystem
mkdir -p rootfs
curl -Lo rootfs.tar.gz $ROOTFS_URL
if file rootfs.tar.gz | grep -q 'gzip compressed data'; then
    tar -xzvf rootfs.tar.gz -C rootfs
else
    echo "Error: rootfs.tar.gz is not in gzip format."
    exit 1
fi
rm rootfs.tar.gz

# Download kernel image
curl -Lo vmlinux $KERNEL_URL
if file vmlinux | grep -q 'Linux kernel x86 boot executable bzImage'; then
    echo "Kernel downloaded successfully."
else
    echo "Error: vmlinux is not a valid kernel image."
    exit 1
fi

# Copy task worker script to rootfs
cp task_worker.py rootfs/root/task_worker.py
echo -e '#!/bin/sh\npython3 /root/task_worker.py' > rootfs/root/init.sh
chmod +x rootfs/root/init.sh

# Create ext4 image
dd if=/dev/zero of=rootfs.ext4 bs=1M count=64
mkfs.ext4 rootfs.ext4
sudo mount -o loop rootfs.ext4 /mnt
sudo cp -r rootfs/* /mnt
sudo umount /mnt

# Prompt for auth key
echo "Please enter your authentication key:"
read -s auth_key
cocore-store-auth-key --key "$auth_key"

echo "Setup complete. Use 'cocore-setup-firecracker' to configure and start Firecracker."
