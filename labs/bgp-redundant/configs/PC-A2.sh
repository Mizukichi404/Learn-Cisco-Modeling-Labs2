hostname PC-A2
ip addr add 10.1.1.11/24 dev eth0
ip link set dev eth0 up
ip route add default via 10.1.1.1
