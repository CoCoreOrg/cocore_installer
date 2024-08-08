#!/bin/bash
#
# This script is meant to be run on the *host* machine to install Firecracker.
#

set -e

VERSION='1.8.0'
ARCH="$(uname -m)"

BIN_DIR='/usr/local/bin'
INSTALL_DIR='/firecracker/releases'
RELEASE_URL="https://github.com/firecracker-microvm/firecracker/releases/download/v${VERSION}"

# Check for prerequisites
#echo 'Checking KVM module...'
#if [ ! "$(lsmod | grep -q kvm)" ]; then
#	echo 'KVM module is not loaded. Please load the KVM module.'
#	exit 1
#fi

echo 'Checking access to /dev/kvm...'
if [ ! -r /dev/kvm ] || [ ! -w /dev/kvm ]; then
	# TODO: setfacl is not installed by default on Ubuntu
	echo 'Access to /dev/kvm is required. Granting access...'
	setfacl -m "u:${USER}:rw" /dev/kvm || (usermod -aG kvm "${USER}" && echo 'Access granted. Please re-login for changes to take effect' && exit 1)
fi

# Download Firecracker and Jailer, if required
release_dir="${INSTALL_DIR}/release-v${VERSION}-${ARCH}"
if [ ! -e "${release_dir}" ]; then
	echo 'Downloading firecracker...'

	mkdir -p "${INSTALL_DIR}"

	archive_name="firecracker-v${VERSION}-${ARCH}.tgz"
	url="${RELEASE_URL}/${archive_name}"

	curl -L -o "${INSTALL_DIR}/${archive_name}" "$url"
	tar xzf "${INSTALL_DIR}/${archive_name}" -C "${INSTALL_DIR}"
	rm "${INSTALL_DIR}/${archive_name}"

	# Link binaries to bin
	if [ ! -f "${release_dir}/firecracker-v${VERSION}-${ARCH}" ]; then
		echo 'Firecracker binary not found in directory.'
		exit 1
	fi
	if [ ! -f "${release_dir}/jailer-v${VERSION}-${ARCH}" ]; then
		echo 'Jailer binary not found in directory.'
		exit 1
	fi

	ln -sfn "${release_dir}/firecracker-v${VERSION}-${ARCH}" "${BIN_DIR}/firecracker"
	ln -sfn "${release_dir}/jailer-v${VERSION}-${ARCH}" "${BIN_DIR}/jailer"
fi

echo
"${BIN_DIR}/firecracker" --version | head -n1
"${BIN_DIR}/jailer" --version | head -n1

