#!/bin/bash

echo "Starting swap setup..." | tee /dev/kmsg
exec > >(tee /dev/kmsg) 2>&1
swapon /root/swapfile
echo "Swap setup complete." | tee /dev/kmsg
exec > >(tee /dev/kmsg) 2>&1

set -e

echo "Starting CoCore initialization..." | tee /dev/kmsg
exec > >(tee /dev/kmsg) 2>&1

echo "Touching dpkg status file..." | tee /dev/kmsg
exec > >(tee /dev/kmsg) 2>&1
touch /var/lib/dpkg/status

echo "Updating apt-get package list..." | tee /dev/kmsg
exec > >(tee /dev/kmsg) 2>&1
apt-get update -y

echo "Installing python3-venv..." | tee /dev/kmsg
exec > >(tee /dev/kmsg) 2>&1
apt-get install -y python3-venv

echo "Setting up Python virtual environment..." | tee /dev/kmsg
exec > >(tee /dev/kmsg) 2>&1
python3 -m venv /root/venv

echo "Activating virtual environment..." | tee /dev/kmsg
exec > >(tee /dev/kmsg) 2>&1
source /root/venv/bin/activate

echo "Installing Python dependencies..." | tee /dev/kmsg
exec > >(tee /dev/kmsg) 2>&1
pip install requests websockets cryptography psutil boto3 urllib3

echo "Running task_worker.py..." | tee /dev/kmsg
exec > >(tee /dev/kmsg) 2>&1
python3 /root/task_worker.py

echo "CoCore initialization complete." | tee /dev/kmsg
exec > >(tee /dev/kmsg) 2>&1
