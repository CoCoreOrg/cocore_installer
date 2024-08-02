#!/bin/bash

set -e

# Variables
FIRECRACKER_VERSION="1.3.1"  # Update to the latest version
ROOTFS_FILE="rootfs.ext4"
KERNEL_FILE="vmlinux"
MOUNT_POINT="mnt"
TASK_WORKER_SCRIPT="cocore_installer/task_worker.py"  # Correct path to task_worker.py

# Install Firecracker and Jailer
install_dir=/firecracker/releases
bin_dir=/usr/bin
release_url="https://github.com/firecracker-microvm/firecracker/releases"
latest=$(basename $(curl -fsSLI -o /dev/null -w %{url_effective} ${release_url}/latest))
arch=$(uname -m)

if [ -d "${install_dir}/release-${latest}" ]; then
    echo "${latest} already installed"
else
    mkdir -p "${install_dir}"
    echo "downloading firecracker-${latest}-${arch}.tgz to ${install_dir}"
    curl -o "${install_dir}/firecracker-${latest}-${arch}.tgz" -L "${release_url}/download/${latest}/firecracker-${latest}-${arch}.tgz"
    pushd "${install_dir}"

    echo "decompressing firecracker-${latest}-${arch}.tgz in ${install_dir}"
    tar -xzf "firecracker-${latest}-${arch}.tgz"
    rm "firecracker-${latest}-${arch}.tgz"

    echo "linking firecracker ${latest}-${arch}"
    sudo ln -sfn "${install_dir}/release-${latest}/firecracker-${latest}-${arch}" "${bin_dir}/firecracker-${latest}-${arch}"
    sudo ln -sfn "${install_dir}/release-${latest}/jailer-${latest}-${arch}" "${bin_dir}/jailer-${latest}-${arch}"
    sudo ln -sfn "${bin_dir}/firecracker-${latest}-${arch}" "${bin_dir}/firecracker"
    sudo ln -sfn "${bin_dir}/jailer-${latest}-${arch}" "${bin_dir}/jailer"

    echo "firecracker ${latest}-${arch}: ready"
    firecracker --version | head -n1
    popd
fi

# Ensure the root filesystem is in place
if [ ! -f $ROOTFS_FILE ]; then
    echo "Root filesystem not found. Downloading..."
    wget https://s3.amazonaws.com/spec.ccfc.min/img/hello/fsfiles/hello-rootfs.ext4 -O rootfs.ext4
fi

# Ensure the kernel is in place
if [ ! -f $KERNEL_FILE ]; then
    echo "Kernel image not found. Downloading..."
    wget https://s3.amazonaws.com/spec.ccfc.min/img/hello/kernel/hello-vmlinux.bin -O vmlinux
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
