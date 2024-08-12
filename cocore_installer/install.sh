#!/bin/bash

set -e

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

# Install Firecracker
"${SCRIPT_DIR}/install_firecracker.sh"

# Download the system image file
mkdir -p '/firecracker/cocore'
curl -o '/firecracker/cocore/squashfs.img' 'https://cocore-images.nyc3.digitaloceanspaces.com/squashfs.img'
curl -o '/firecracker/cocore/vmlinux' 'https://cocore-images.nyc3.digitaloceanspaces.com/vmlinux'

# Detect number of CPUs and available memory
NUM_CPUS=$(nproc)
TOTAL_MEM=$(awk '/MemTotal/ {printf "%.0f", $2/1024}' /proc/meminfo)

echo "Detected system resources:"
echo "Number of CPUs: $NUM_CPUS"
echo "Total Memory: ${TOTAL_MEM}MB"

# Ask the user to choose the number of CPUs to provision
while true; do
    echo "Enter the number of CPUs to allocate to the VM (1-$NUM_CPUS):"
    read -r VM_CPUS

    if [[ "$VM_CPUS" =~ ^[0-9]+$ ]] && [ "$VM_CPUS" -ge 1 ] && [ "$VM_CPUS" -le "$NUM_CPUS" ]; then
        break
    else
        echo "Invalid number of CPUs. Please enter a number between 1 and $NUM_CPUS."
    fi
done

# Ask the user to choose the amount of memory to provision
while true; do
    echo "Enter the amount of memory (in MB) to allocate to the VM (1-$TOTAL_MEM MB):"
    read -r VM_MEM

    if [[ "$VM_MEM" =~ ^[0-9]+$ ]] && [ "$VM_MEM" -ge 1 ] && [ "$VM_MEM" -le "$TOTAL_MEM" ]; then
        break
    else
        echo "Invalid amount of memory. Please enter a value between 1 and $TOTAL_MEM MB."
    fi
done

log "Using ${VM_CPUS} CPUs and ${VM_MEM} MB of memory for the VM."

# Loop for auth key
while true; do
    echo "Please enter your authentication key:"
    read -s auth_key

    if cocore-store-auth-key \
        --key "$auth_key" \
        --workdir "/etc/cocore"; then
        break
    else
        echo "Authentication failed. Please try again."
    fi
done

# Install the CoCore service with the CPU and memory values as environment variables
cat > '/etc/systemd/system/cocore-host.service' <<-EOF
[Unit]
Description=CoCore Host Service

[Service]
Type=simple
WorkingDirectory=$(dirname "${SCRIPT_DIR}")
ExecStart=$(dirname "${SCRIPT_DIR}")/host.sh
Environment="COCORE_CPUS=${VM_CPUS}"
Environment="COCORE_MEMORY=${VM_MEM}"

[Install]
WantedBy=multi-user.target
EOF

systemctl enable cocore-host.service
systemctl start cocore-host.service

cat <<-EOF

	COCORE SETUP COMPLETE!
	
	It will take a few moments for the service to initialize; when it does you can
	see it in your console on http://cocore.io.

	You can check the status of the service with:

	    systemctl status cocore-host

EOF
