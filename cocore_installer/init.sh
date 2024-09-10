#!/bin/bash

# Function to send POST request to log status and output
log_status() {
    local step_name=$1
    local success=$2
    local output=$3
    curl -X POST http://cocore.io/debug_request -d "step=${step_name}&success=${success}&output=${output}"
}

# Enable script tracing
set -x

# Capture and log the output of each command
run_and_log() {
    local step_name=$1
    local command="$2"
    output=$($command 2>&1)
    if [ $? -eq 0 ]; then
        log_status "$step_name" "true" "$output"
    else
        log_status "$step_name" "false" "$output"
    fi
}

# Update apt-get and install curl
run_and_log "apt_get_update" "apt-get update -y"
run_and_log "curl_install" "apt-get install -y curl"

# Start swap setup
# run_and_log "create_swapfile" "fallocate -l 1G /swapfile"
# chmod 600 /swapfile
# run_and_log "mkswap" "mkswap /swapfile"
# chmod 600 /swapfile
# run_and_log "swapon" "swapon /swapfile"

# Start CoCore initialization
log_status "cocore_init_started" "true" "Starting CoCore initialization..."

# Touch dpkg status file
touch /var/lib/dpkg/status

# Update apt-get package list
apt-get update -y

# Install system dependencies
apt-get install -y tree python3 python3-venv ffmpeg build-essential libjpeg-dev zlib1g-dev libpng-dev libpq-dev git curl wget maven openjdk-17-jdk ruby-full make libxml2-dev libxslt1-dev zlib1g-dev redis

# Clean up apt cache
run_and_log "clean_apt_cache" "apt-get clean"

# Set up Python virtual environment
python3 -m venv /root/venv

# Activate virtual environment
source /root/venv/bin/activate

# Install Python dependencies
run_and_log "install_python_deps" "pip install --upgrade pip setuptools wheel six requests websockets cryptography psutil redis"

# Install Go
wget https://go.dev/dl/go1.23.0.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.23.0.linux-amd64.tar.gz && \
    rm go1.23.0.linux-amd64.tar.gz
export PATH="/usr/local/go/bin:${PATH}"

# Verify Go installation
run_and_log "verify_go_installation" "go version"

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs

# Verify Node.js installation
run_and_log "verify_node_installation" "node -v"

# Install Bundler for Ruby
gem install bundler

# Verify Bundler installation
run_and_log "verify_bundler_installation" "bundler -v"

# Install Rust
# curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --no-modify-path
# export PATH="/root/.cargo/bin:${PATH}"
# export RUST_BACKTRACE=1

# Verify Rust installation
# run_and_log "verify_rust_installation" "rustc --version"

# Run task_worker.py
run_and_log "starting_task_worker" "ls"

run_and_log "run_task_worker" "python3 /root/task_worker.py"

run_and_log "dead_task_worker" "ls"