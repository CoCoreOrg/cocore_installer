#!/bin/bash

set -ex

HOST_IFACE=elo1

ip link del tap0 2> /dev/null || true
ip tuntap add dev tap0 mode tap
ip addr add 172.16.0.1/30 dev tap0
ip link set dev tap0 up

echo 1 > /proc/sys/net/ipv4/ip_forward

iptables -t nat -D POSTROUTING -o "$HOST_IFACE" -j MASQUERADE || true
iptables -D FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT || true
iptables -D FORWARD -i tap0 -o "$HOST_IFACE" -j ACCEPT || true
iptables -t nat -A POSTROUTING -o "$HOST_IFACE" -j MASQUERADE
iptables -I FORWARD 1 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
iptables -I FORWARD 1 -i tap0 -o "$HOST_IFACE" -j ACCEPT

