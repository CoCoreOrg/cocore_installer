#!/bin/bash
#
# This script is meant to be run on the *host machine* to add the tap0 network device.
#

set -e

HOST_DEVICE="$1"
TAP_DEVICE="$2"
TAP_IP="$3"

if [ -z "${HOST_DEVICE}" ] || [ -z "${TAP_DEVICE}" ] || [ -z "${TAP_IP}" ]; then
	echo "USAGE: $0 <host_interface> <tap_device> <tap_ip_with_netmask>"
    echo
	echo "  Example: $0 eth0 tap1 172.16.0.1/31"
	echo
	exit 1
fi

ip link del "${TAP_DEVICE}" 2> /dev/null || true
ip tuntap add dev "${TAP_DEVICE}" mode tap
ip addr add "${TAP_IP}" dev "${TAP_DEVICE}"
ip link set dev "${TAP_DEVICE}" up

echo 1 > /proc/sys/net/ipv4/ip_forward

iptables -t nat -D POSTROUTING -o "${HOST_DEVICE}" -j MASQUERADE &>/dev/null || true
iptables -D FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT &>/dev/null || true
iptables -D FORWARD -i "${TAP_DEVICE}" -o "${HOST_DEVICE}" &>/dev/null || true

iptables -t nat -A POSTROUTING -o "${HOST_DEVICE}" -j MASQUERADE
iptables -I FORWARD 1 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
iptables -I FORWARD 1 -i "${TAP_DEVICE}" -o "${HOST_DEVICE}" -j ACCEPT

