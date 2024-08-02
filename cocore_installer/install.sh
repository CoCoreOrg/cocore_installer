#!/bin/bash

set -e

# Variables
FIRECRACKER_VERSION="1.8.0"  # Specify the desired version
ROOTFS_FILE="rootfs.ext4"
KERNEL_FILE="vmlinux"
MOUNT_POINT="mnt"
TASK_WORKER_SCRIPT="cocore_installer/task_worker.py"  # Correct path to task_worker.py

# Install Firecracker and Jailer
install_dir=/firecracker/releases
bin_dir=/usr/bin
release_url="https://github.com/firecracker-microvm/firecracker/releases/download/v${FIRECRACKER_VERSION}"
arch=$(uname -m)

if [ -d "${install_dir}/release-v${FIRECRACKER_VERSION}" ]; then
    echo "Firecracker ${FIRECRACKER_VERSION} already installed"
else
    mkdir -p "${install_dir}"
    download_url="${release_url}/firecracker-v${FIRECRACKER_VERSION}-${arch}.tgz"
    echo "Attempting to download Firecracker from URL: ${download_url}"
    wget -O "${install_dir}/firecracker-v${FIRECRACKER_VERSION}-${arch}.tgz" "${download_url}"
    pushd "${install_dir}"

    echo "Decompressing firecracker-v${FIRECRACKER_VERSION}-${arch}.tgz in ${install_dir}"
    tar -xzf "firecracker-v${FIRECRACKER_VERSION}-${arch}.tgz"
    rm "firecracker-v${FIRECRACKER_VERSION}-${arch}.tgz"

    echo "Linking firecracker ${FIRECRACKER_VERSION}-${arch}"
    sudo ln -sfn "${install_dir}/firecracker-v${FIRECRACKER_VERSION}-${arch}" "${bin_dir}/firecracker-${FIRECRACKER_VERSION}-${arch}"
    sudo ln -sfn "${install_dir}/jailer-v${FIRECRACKER_VERSION}-${arch}" "${bin_dir}/jailer-${FIRECRACKER_VERSION}-${arch}"
    sudo ln -sfn "${bin_dir}/firecracker-${FIRECRACKER_VERSION}-${arch}" "${bin_dir}/firecracker"
    sudo ln -sfn "${bin_dir}/jailer-${FIRECRACKER_VERSION}-${arch}" "${bin_dir}/jailer"

    echo "firecracker ${FIRECRACKER_VERSION}-${arch}: ready"
    ls -l "${bin_dir}/firecracker-${FIRECRACKER_VERSION}-${arch}"
    file "${bin_dir}/firecracker-${FIRECRACKER_VERSION}-${arch}"
    file "${bin_dir}/firecracker"
    firecracker --version | head -n1
    popd
fi

# Ensure the root filesystem is in place
if [ ! -f $ROOTFS_FILE ]; then
    echo "Root filesystem not found. Downloading..."
    rootfs_url="https://s3.amazonaws.com/spec.ccfc.min/img/hello/fsfiles/hello-rootfs.ext4"
    echo "Attempting to download root filesystem from URL: ${rootfs_url}"
    wget $rootfs_url -O rootfs.ext4
fi

# Ensure the kernel is in place
if [ ! -f $KERNEL_FILE ]; then
    echo "Kernel image not found. Downloading..."
    kernel_url="https://s3.amazonaws.com/spec.ccfc.min/img/hello/kernel/hello-vmlinux.bin"
    echo "Attempting to download kernel from URL: ${kernel_url}"
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
