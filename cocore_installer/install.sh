#!/bin/bash

set -e

# Variables
FIRECTL_VERSION="0.1.1"
FIRECTL_BIN="/usr/local/bin/firectl"
ARCH=$(uname -m)
MOUNT_POINT="mnt"
TASK_WORKER_SCRIPT="cocore_installer/task_worker.py"  # Correct path to task_worker.py
API_SOCKET="/tmp/firecracker.socket"
LOGFILE="./cocore_installer/firecracker.log"

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

# Install Docker if not already installed
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Installing Docker..."
    sudo apt-get update
    sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
    sudo apt-get update
    sudo apt-get install -y docker-ce
    sudo systemctl start docker
    sudo systemctl enable docker
fi

# Download Firecracker binary
echo "Downloading Firecracker..."
curl -Lo /usr/local/bin/firecracker https://github.com/firecracker-microvm/firecracker/releases/download/v1.8.0/firecracker-v1.8.0-${ARCH}
chmod +x /usr/local/bin/firecracker

# Build firectl using Docker
echo "Cloning firectl repository..."
git clone https://github.com/firecracker-microvm/firectl.git
cd firectl

echo "Building firectl using Docker..."
docker run --rm -v "$(pwd)":/usr/src/firectl -w /usr/src/firectl golang:1.14 go build -o firectl .

echo "Moving firectl binary to /usr/local/bin..."
mv firectl /usr/local/bin/firectl
chmod +x /usr/local/bin/firectl
cd ..
rm -rf firectl

# Download Kernel and Root Filesystem
echo "Downloading kernel and root filesystem..."
kernel_url="https://s3.amazonaws.com/spec.ccfc.min/img/hello/kernel/hello-vmlinux.bin"
rootfs_url="https://s3.amazonaws.com/spec.ccfc.min/img/hello/fsfiles/hello-rootfs.ext4"

wget -O "vmlinux" "${kernel_url}" || { echo "Failed to download kernel"; exit 1; }
wget -O "rootfs.ext4" "${rootfs_url}" || { echo "Failed to download root filesystem"; exit 1; }

# Ensure the root filesystem is in place
if [ ! -f rootfs.ext4 ]; then
    echo "Root filesystem not found. Downloading..."
    wget $rootfs_url -O rootfs.ext4
fi

# Ensure the kernel is in place
if [ ! -f vmlinux ]; then
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
sudo mount -o loop rootfs.ext4 $MOUNT_POINT
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
