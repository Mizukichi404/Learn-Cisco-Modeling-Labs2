hostname PC-B1
ip addr add 10.2.2.10/24 dev eth0
ip link set dev eth0 up
ip route add default via 10.2.2.1
