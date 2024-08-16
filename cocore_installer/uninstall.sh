#!/bin/bash

set -e

echo "Starting CoCore uninstallation..."

# Stop and Clean Up Firecracker Processes
echo "Terminating Firecracker processes..."
pkill -f /usr/local/bin/firecracker || true
if [ -e /tmp/firecracker.socket ]; then
    rm /tmp/firecracker.socket
fi

# Unmount and Remove Disk Images
MOUNT_POINT="mnt"
if mountpoint -q $MOUNT_POINT; then
    echo "Unmounting $MOUNT_POINT..."
    sudo umount $MOUNT_POINT
fi
echo "Removing disk images and related files..."
rm -f ubuntu-22.04.ext4 vmlinux firecracker.rsa

# Remove Installed Packages and Dependencies
if [ -d "venv" ]; then
    echo "Removing Python packages..."
    source venv/bin/activate
    pip uninstall -y requests requests-unixsocket psutil six urllib3 cryptography websockets tornado cocore_installer
    deactivate
fi

# Remove Python Virtual Environment
echo "Removing Python virtual environment..."
rm -rf venv

# Remove Firecracker Binaries
echo "Removing Firecracker binaries..."
sudo rm -f /usr/local/bin/firecracker
sudo rm -f /usr/local/bin/jailer

# Remove Firecracker Directory
echo "Removing Firecracker directory..."
sudo rm -rf /firecracker

# Delete Configuration and Authentication Files
echo "Removing configuration and authentication files..."
sudo rm -rf /etc/cocore

# Clean Up Network Configuration
echo "Cleaning up network configuration..."
HOST_IFACE=eth0
sudo ip link del tap0 2> /dev/null || true
sudo iptables -t nat -D POSTROUTING -o "$HOST_IFACE" -j MASQUERADE || true
sudo iptables -D FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT || true
sudo iptables -D FORWARD -i tap0 -o "$HOST_IFACE" -j ACCEPT || true

# Remove Temporary and Log Files
echo "Removing temporary and log files..."
rm -rf ./cocore_installer/firecracker.log
rm -rf $MOUNT_POINT

# Remove CoCore systemd service
echo "Removing CoCore systemd service..."
sudo systemctl stop cocore-host.service
sudo systemctl disable cocore-host.service
sudo rm -f /etc/systemd/system/cocore-host.service
sudo systemctl daemon-reload
sudo systemctl reset-failed

echo "CoCore uninstallation completed."
