#!/bin/bash

set -e

echo COCORE

echo 'nameserver 8.8.8.8' > /etc/resolv.conf
ip addr add 172.16.0.2/24 dev eth0
ip link set eth0 up
ip route add default via 172.16.0.1 dev eth0
echo 1 > /root/network_configured

sleep 1

touch /var/lib/dpkg/status
apt-get update -y

# Determine the correct package manager and install venv
if command -v apt-get &>/dev/null; then
    apt-get install -y python3-venv
elif command -v yum &>/dev/null; then
    yum install -y python3-venv
elif command -v dnf &>/dev/null; then
    dnf install -y python3-venv
elif command -v zypper &>/dev/null; then
    zypper install -y python3-venv
elif command -v pacman &>/dev/null; then
    pacman -S --noconfirm python-virtualenv
else
    echo "No supported package manager found for installing python3-venv."
    exit 1
fi

python3 -m venv /root/venv

source /root/venv/bin/activate

pip install requests websockets cryptography

python3 /root/task_worker.py
