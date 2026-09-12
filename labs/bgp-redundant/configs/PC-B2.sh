hostname PC-B2
ip addr add 10.2.2.11/24 dev eth0
ip link set dev eth0 up
ip route add default via 10.2.2.1
