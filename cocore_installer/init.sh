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
log_status "swap_setup_started" "true" "Starting swap setup..."
run_and_log "ls_env" "env"
run_and_log "ls_root" "ls /"
run_and_log "ls_root_dir" "ls /root"
run_and_log "swapon" "swapon /root/swapfile"

# Start CoCore initialization
log_status "cocore_init_started" "true" "Starting CoCore initialization..."

# Touch dpkg status file
run_and_log "touch_dpkg" "touch /var/lib/dpkg/status"

# Update apt-get package list
run_and_log "apt_get_update_2" "apt-get update -y"

# Install system dependencies
run_and_log "install_dependencies" "apt-get install -y tree python3 python3-venv ffmpeg build-essential libjpeg-dev zlib1g-dev libpng-dev libpq-dev git curl wget maven openjdk-17-jdk ruby-full"

# Clean up apt cache
run_and_log "clean_apt_cache" "apt-get clean"

# Set up Python virtual environment
run_and_log "setup_venv" "python3 -m venv /root/venv"

# Activate virtual environment
run_and_log "activate_venv" "source /root/venv/bin/activate"

# Install Python dependencies
run_and_log "install_python_deps" "pip install --upgrade pip setuptools wheel six requests websockets cryptography psutil"

# Install Go
run_and_log "install_go" "wget https://go.dev/dl/go1.23.0.linux-amd64.tar.gz && tar -C /usr/local -xzf go1.23.0.linux-amd64.tar.gz && rm go1.23.0.linux-amd64.tar.gz"

# Install Node.js
run_and_log "install_node" "curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && apt-get install -y nodejs"

# Install Bundler for Ruby
run_and_log "install_bundler" "gem install bundler"

# Install Rust
run_and_log "install_rust" "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y"

# Check structure
run_and_log "check_directory" "tree /usr/src"

# Run task_worker.py
run_and_log "run_task_worker" "python3 /root/task_worker.py"

log_status "cocore_init_complete" "true" "CoCore initialization complete."
