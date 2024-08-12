#!/bin/bash

echo "Starting swap setup..." | tee /dev/kmsg
swapon /root/swapfile
echo "Swap setup complete." | tee /dev/kmsg

set -e

echo "Starting CoCore initialization..." | tee /dev/kmsg

echo "Touching dpkg status file..." | tee /dev/kmsg
touch /var/lib/dpkg/status

echo "Updating apt-get package list..." | tee /dev/kmsg
apt-get update -y

echo "Installing python3-venv..." | tee /dev/kmsg
apt-get install -y python3-venv

echo "Setting up Python virtual environment..." | tee /dev/kmsg
python3 -m venv /root/venv

echo "Activating virtual environment..." | tee /dev/kmsg
source /root/venv/bin/activate

echo "Installing Python dependencies..." | tee /dev/kmsg
pip install requests websockets cryptography psutil boto3 urllib3 setuptools requests botocore certifi charset-normalizer idna typing-extensions packaging python-dateutil cryptography pyyaml aiobotocore six s3transfer numpy grpcio-status fsspec scikit-learn

echo "Running task_worker.py..." | tee /dev/kmsg
python3 /root/task_worker.py

echo "CoCore initialization complete." | tee /dev/kmsg
