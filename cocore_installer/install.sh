#!/bin/bash

set -e

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

# Install Firecracker
"${SCRIPT_DIR}/install_firecracker.sh"

# Download the system image file
mkdir -p '/firecracker/cocore'
curl -o '/firecracker/cocore/squashfs.img' 'https://cocore-images.nyc3.digitaloceanspaces.com/squashfs.img'
curl -o '/firecracker/cocore/vmlinux' 'https://cocore-images.nyc3.digitaloceanspaces.com/vmlinux'

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

echo "Setup complete. Use 'cocore-setup-firecracker' to configure and start Firecracker."

