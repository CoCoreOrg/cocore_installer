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

echo "Installing system dependencies..." | tee /dev/kmsg
exec > >(tee /dev/kmsg) 2>&1
apt-get install -y \
    python3-venv \
    ffmpeg \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libpq-dev \
    git \
    curl \
    wget \
    maven \
    openjdk-17-jdk \
    ruby-full

echo "Cleaning up apt cache..." | tee /dev/kmsg
exec > >(tee /dev/kmsg) 2>&1
apt-get clean

echo "Setting up Python virtual environment..." | tee /dev/kmsg
exec > >(tee /dev/kmsg) 2>&1
python3 -m venv /root/venv

echo "Activating virtual environment..." | tee /dev/kmsg
exec > >(tee /dev/kmsg) 2>&1
source /root/venv/bin/activate

echo "Installing Python dependencies..." | tee /dev/kmsg
exec > >(tee /dev/kmsg) 2>&1
pip install --upgrade pip setuptools wheel six requests websockets cryptography psutil

echo "Installing Go..." | tee /dev/kmsg
exec > >(tee /dev/kmsg) 2>&1
wget https://go.dev/dl/go1.23.0.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.23.0.linux-amd64.tar.gz && \
    rm go1.23.0.linux-amd64.tar.gz
export PATH="/usr/local/go/bin:${PATH}"

echo "Installing Node.js..." | tee /dev/kmsg
exec > >(tee /dev/kmsg) 2>&1
curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs

echo "Installing Bundler for Ruby..." | tee /dev/kmsg
exec > >(tee /dev/kmsg) 2>&1
gem install bundler

echo "Installing Rust..." | tee /dev/kmsg
exec > >(tee /dev/kmsg) 2>&1
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
export PATH="/root/.cargo/bin:${PATH}"
export RUST_BACKTRACE=1

echo "Running task_worker.py..." | tee /dev/kmsg
exec > >(tee /dev/kmsg) 2>&1
python3 /usr/src/app/task_worker.py

echo "CoCore initialization complete." | tee /dev/kmsg
exec > >(tee /dev/kmsg) 2>&1
