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

# Install the CoCore service
cat > '/etc/systemd/system/cocore-host.service' <<-EOF
[Unit]
Description=CoCore Host Service

[Service]
Type=simple
WorkingDirectory=$(dirname "${SCRIPT_DIR}")
ExecStart=$(dirname "${SCRIPT_DIR}")/host.sh

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

