hostname PC-A1
ip addr add 10.1.1.10/24 dev eth0
ip link set dev eth0 up
ip route add default via 10.1.1.1
