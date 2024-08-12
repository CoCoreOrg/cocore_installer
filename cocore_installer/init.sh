#!/bin/bash

set -e

echo COCORE

touch /var/lib/dpkg/status

# The task worker runs in the VM; the package manager will always be APT/Ubuntu
apt-get update -y
apt-get install -y python3-venv

python3 -m venv /root/venv

source /root/venv/bin/activate

pip install requests websockets cryptography psutil boto3 urllib3 setuptools requests botocore certifi charset-normalizer idna typing-extensions packaging python-dateutil cryptography pyyaml aiobotocore six s3transfer pip numpy grpcio-status fsspec scikit-learn transformers

python3 /root/task_worker.py
