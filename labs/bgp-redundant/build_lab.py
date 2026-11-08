#!/usr/bin/env python3
"""Generate the CML2 importable YAML for the redundant BGP/iBGP/OSPF lab."""

from pathlib import Path

OUT = Path(__file__).with_name("bgp-ibgp-ospf-redundant.yaml")

IOS_COMMON = """
no ip domain lookup
ip domain name lab.local
!
enable secret cisco
username cisco privilege 15 secret cisco
!
service timestamps debug datetime msec
service timestamps log datetime msec
!
ip cef
!
"""

IOS_LINES = """
!
line con 0
 exec-timeout 0 0
 logging synchronous
line vty 0 4
 login local
 transport input telnet ssh
!
end
"""


def iface(name, desc, ip, extra=""):
    extra_lines = ""
    if extra:
        extra_lines = extra.rstrip() + "\n"
    return f"""interface {name}
 description {desc}
 ip address {ip}
{extra_lines} duplex auto
 speed auto
 media-type rj45
 no shutdown
!
"""


def ios_node(nid, label, x, y, config, n_phys):
    ifaces = [
        "    - id: i0\n      label: Loopback0\n      type: loopback",
    ]
    for slot in range(n_phys):
        ifaces.append(
            f"    - id: i{slot + 1}\n"
            f"      label: GigabitEthernet0/{slot}\n"
            f"      slot: {slot}\n"
            f"      type: physical"
        )
    cfg = indent(config.strip("\n") + "\n", 6)
    iface_yaml = "\n".join(ifaces)
    return f"""  - boot_disk_size: 0
    configuration: |-
{cfg}
    cpu_limit: 100
    cpus: 1
    data_volume: 0
    hide_links: false
    id: {nid}
    image_definition: null
    label: {label}
    node_definition: iosv
    ram: 512
    tags: []
    x: {x}
    y: {y}
    interfaces:
{iface_yaml}
"""


def alpine_node(nid, label, x, y, hostname, ip, gw):
    config = f"""# this is a shell script which will be sourced at boot
hostname {hostname}
USERNAME=cisco
PASSWORD=cisco
ip addr add {ip} dev eth0
ip link set dev eth0 up
ip route add default via {gw}
"""
    cfg = indent(config, 6)
    return f"""  - boot_disk_size: 16
    configuration: |-
{cfg}
    cpu_limit: 100
    cpus: 1
    data_volume: 0
    hide_links: false
    id: {nid}
    image_definition: null
    label: {label}
    node_definition: alpine
    ram: 256
    tags: []
    x: {x}
    y: {y}
    interfaces:
    - id: i0
      label: eth0
      slot: 0
      type: physical
"""


def ums_node(nid, label, x, y, ums_id):
    ifaces = "\n".join(
        f"    - id: i{i}\n      label: port{i}\n      slot: {i}\n      type: physical"
        for i in range(8)
    )
    return f"""  - boot_disk_size: 0
    configuration: {ums_id}
    cpu_limit: 100
    cpus: 0
    data_volume: 0
    hide_links: false
    id: {nid}
    image_definition: null
    label: {label}
    node_definition: unmanaged_switch
    ram: 0
    tags: []
    x: {x}
    y: {y}
    interfaces:
{ifaces}
"""


def indent(text, n):
    pad = " " * n
    return "\n".join(pad + line if line else pad for line in text.splitlines())


CE_A = f"""!
hostname CE-A
!
{IOS_COMMON}
interface Loopback0
 description Router-ID / BGP RID
 ip address 1.1.1.1 255.255.255.255
!
{iface("GigabitEthernet0/0", "eBGP to PE1 (AS65000) PRIMARY", "192.168.13.1 255.255.255.252")}
{iface("GigabitEthernet0/1", "eBGP to PE2 (AS65000) BACKUP", "192.168.14.1 255.255.255.252")}
{iface("GigabitEthernet0/2", "Site-A user LAN 10.1.1.0/24", "10.1.1.1 255.255.255.0")}
router bgp 65001
 bgp router-id 1.1.1.1
 bgp log-neighbor-changes
 network 10.1.1.0 mask 255.255.255.0
 neighbor 192.168.13.2 remote-as 65000
 neighbor 192.168.13.2 description PE1-primary
 neighbor 192.168.13.2 weight 200
 neighbor 192.168.14.2 remote-as 65000
 neighbor 192.168.14.2 description PE2-backup
 neighbor 192.168.14.2 weight 100
!
{IOS_LINES}
"""

CE_B = f"""!
hostname CE-B
!
{IOS_COMMON}
interface Loopback0
 description Router-ID / BGP RID
 ip address 2.2.2.2 255.255.255.255
!
{iface("GigabitEthernet0/0", "eBGP to PE1 (AS65000) BACKUP", "192.168.23.1 255.255.255.252")}
{iface("GigabitEthernet0/1", "eBGP to PE2 (AS65000) PRIMARY", "192.168.24.1 255.255.255.252")}
{iface("GigabitEthernet0/2", "Site-B user LAN 10.2.2.0/24", "10.2.2.1 255.255.255.0")}
router bgp 65002
 bgp router-id 2.2.2.2
 bgp log-neighbor-changes
 network 10.2.2.0 mask 255.255.255.0
 neighbor 192.168.23.2 remote-as 65000
 neighbor 192.168.23.2 description PE1-backup
 neighbor 192.168.23.2 weight 100
 neighbor 192.168.24.2 remote-as 65000
 neighbor 192.168.24.2 description PE2-primary
 neighbor 192.168.24.2 weight 200
!
{IOS_LINES}
"""

OSPF_P2P = """ ip ospf network point-to-point
 ip ospf hello-interval 3
 ip ospf dead-interval 12
"""

PE1 = f"""!
hostname PE1
!
{IOS_COMMON}
interface Loopback0
 description Router-ID / iBGP source
 ip address 3.3.3.3 255.255.255.255
!
{iface("GigabitEthernet0/0", "OSPF to P", "10.0.35.1 255.255.255.252", OSPF_P2P)}
{iface("GigabitEthernet0/1", "OSPF to PE2 (redundant core)", "10.0.34.1 255.255.255.252", OSPF_P2P)}
{iface("GigabitEthernet0/2", "eBGP to CE-A (AS65001)", "192.168.13.2 255.255.255.252")}
{iface("GigabitEthernet0/3", "eBGP to CE-B (AS65002)", "192.168.23.2 255.255.255.252")}
router ospf 1
 router-id 3.3.3.3
 passive-interface default
 no passive-interface GigabitEthernet0/0
 no passive-interface GigabitEthernet0/1
 network 3.3.3.3 0.0.0.0 area 0
 network 10.0.34.0 0.0.0.3 area 0
 network 10.0.35.0 0.0.0.3 area 0
!
router bgp 65000
 bgp router-id 3.3.3.3
 bgp log-neighbor-changes
 neighbor 4.4.4.4 remote-as 65000
 neighbor 4.4.4.4 description PE2-iBGP
 neighbor 4.4.4.4 update-source Loopback0
 neighbor 4.4.4.4 next-hop-self
 neighbor 5.5.5.5 remote-as 65000
 neighbor 5.5.5.5 description P-iBGP
 neighbor 5.5.5.5 update-source Loopback0
 neighbor 5.5.5.5 next-hop-self
 neighbor 192.168.13.1 remote-as 65001
 neighbor 192.168.13.1 description CE-A
 neighbor 192.168.13.1 default-originate
 neighbor 192.168.23.1 remote-as 65002
 neighbor 192.168.23.1 description CE-B
 neighbor 192.168.23.1 default-originate
!
{IOS_LINES}
"""

PE2 = f"""!
hostname PE2
!
{IOS_COMMON}
interface Loopback0
 description Router-ID / iBGP source
 ip address 4.4.4.4 255.255.255.255
!
{iface("GigabitEthernet0/0", "OSPF to P", "10.0.45.1 255.255.255.252", OSPF_P2P)}
{iface("GigabitEthernet0/1", "OSPF to PE1 (redundant core)", "10.0.34.2 255.255.255.252", OSPF_P2P)}
{iface("GigabitEthernet0/2", "eBGP to CE-A (AS65001)", "192.168.14.2 255.255.255.252")}
{iface("GigabitEthernet0/3", "eBGP to CE-B (AS65002)", "192.168.24.2 255.255.255.252")}
router ospf 1
 router-id 4.4.4.4
 passive-interface default
 no passive-interface GigabitEthernet0/0
 no passive-interface GigabitEthernet0/1
 network 4.4.4.4 0.0.0.0 area 0
 network 10.0.34.0 0.0.0.3 area 0
 network 10.0.45.0 0.0.0.3 area 0
!
router bgp 65000
 bgp router-id 4.4.4.4
 bgp log-neighbor-changes
 neighbor 3.3.3.3 remote-as 65000
 neighbor 3.3.3.3 description PE1-iBGP
 neighbor 3.3.3.3 update-source Loopback0
 neighbor 3.3.3.3 next-hop-self
 neighbor 5.5.5.5 remote-as 65000
 neighbor 5.5.5.5 description P-iBGP
 neighbor 5.5.5.5 update-source Loopback0
 neighbor 5.5.5.5 next-hop-self
 neighbor 192.168.14.1 remote-as 65001
 neighbor 192.168.14.1 description CE-A
 neighbor 192.168.14.1 default-originate
 neighbor 192.168.24.1 remote-as 65002
 neighbor 192.168.24.1 description CE-B
 neighbor 192.168.24.1 default-originate
!
{IOS_LINES}
"""

P = f"""!
hostname P
!
{IOS_COMMON}
interface Loopback0
 description Router-ID / iBGP source
 ip address 5.5.5.5 255.255.255.255
!
{iface("GigabitEthernet0/0", "OSPF to PE1", "10.0.35.2 255.255.255.252", OSPF_P2P)}
{iface("GigabitEthernet0/1", "OSPF to PE2", "10.0.45.2 255.255.255.252", OSPF_P2P)}
router ospf 1
 router-id 5.5.5.5
 passive-interface default
 no passive-interface GigabitEthernet0/0
 no passive-interface GigabitEthernet0/1
 network 5.5.5.5 0.0.0.0 area 0
 network 10.0.35.0 0.0.0.3 area 0
 network 10.0.45.0 0.0.0.3 area 0
!
router bgp 65000
 bgp router-id 5.5.5.5
 bgp log-neighbor-changes
 neighbor 3.3.3.3 remote-as 65000
 neighbor 3.3.3.3 description PE1-iBGP
 neighbor 3.3.3.3 update-source Loopback0
 neighbor 3.3.3.3 next-hop-self
 neighbor 4.4.4.4 remote-as 65000
 neighbor 4.4.4.4 description PE2-iBGP
 neighbor 4.4.4.4 update-source Loopback0
 neighbor 4.4.4.4 next-hop-self
!
{IOS_LINES}
"""

LINKS = [
    ("l0", "n0", "n2", "i1", "i3", "CE-A-GigabitEthernet0/0<->PE1-GigabitEthernet0/2"),
    ("l1", "n0", "n3", "i2", "i3", "CE-A-GigabitEthernet0/1<->PE2-GigabitEthernet0/2"),
    ("l2", "n0", "n5", "i3", "i0", "CE-A-GigabitEthernet0/2<->SW-A-port0"),
    ("l3", "n1", "n2", "i1", "i4", "CE-B-GigabitEthernet0/0<->PE1-GigabitEthernet0/3"),
    ("l4", "n1", "n3", "i2", "i4", "CE-B-GigabitEthernet0/1<->PE2-GigabitEthernet0/3"),
    ("l5", "n1", "n6", "i3", "i0", "CE-B-GigabitEthernet0/2<->SW-B-port0"),
    ("l6", "n2", "n4", "i1", "i1", "PE1-GigabitEthernet0/0<->P-GigabitEthernet0/0"),
    ("l7", "n3", "n4", "i1", "i2", "PE2-GigabitEthernet0/0<->P-GigabitEthernet0/1"),
    ("l8", "n2", "n3", "i2", "i2", "PE1-GigabitEthernet0/1<->PE2-GigabitEthernet0/1"),
    ("l9", "n7", "n5", "i0", "i1", "PC-A1-eth0<->SW-A-port1"),
    ("l10", "n8", "n5", "i0", "i2", "PC-A2-eth0<->SW-A-port2"),
    ("l11", "n9", "n6", "i0", "i1", "PC-B1-eth0<->SW-B-port1"),
    ("l12", "n10", "n6", "i0", "i2", "PC-B2-eth0<->SW-B-port2"),
]


def links_yaml():
    blocks = []
    for lid, n1, n2, i1, i2, label in LINKS:
        blocks.append(
            f"""  - id: {lid}
    n1: {n1}
    n2: {n2}
    i1: {i1}
    i2: {i2}
    label: {label}
    conditioning: {{}}"""
        )
    return "\n".join(blocks)


def main():
    nodes = "".join(
        [
            ios_node("n0", "CE-A", -360, -80, CE_A, 3),
            ios_node("n1", "CE-B", 360, -80, CE_B, 3),
            ios_node("n2", "PE1", -80, -280, PE1, 4),
            ios_node("n3", "PE2", -80, 120, PE2, 4),
            ios_node("n4", "P", 80, -80, P, 2),
            ums_node("n5", "SW-A", -560, -80, "ums-7c1a9b2e-a1"),
            ums_node("n6", "SW-B", 560, -80, "ums-7c1a9b2e-b2"),
            alpine_node("n7", "PC-A1", -760, -260, "PC-A1", "10.1.1.10/24", "10.1.1.1"),
            alpine_node("n8", "PC-A2", -760, 80, "PC-A2", "10.1.1.11/24", "10.1.1.1"),
            alpine_node("n9", "PC-B1", 760, -260, "PC-B1", "10.2.2.10/24", "10.2.2.1"),
            alpine_node("n10", "PC-B2", 760, 80, "PC-B2", "10.2.2.11/24", "10.2.2.1"),
        ]
    )

    lab = f"""lab:
  description: Redundant dual-homed BGP lab with OSPF underlay, iBGP full mesh, eBGP
    to two customer sites, and user PCs for end-to-end ping/traceroute.
  notes: |
    Import this file in CML2 (Lab Manager > Import). Start all nodes and wait
    until OSPF (PE1/PE2/P) and BGP sessions are Established.

    AS65001 Site-A users 10.1.1.0/24  <->  AS65000 ISP  <->  AS65002 Site-B users 10.2.2.0/24

    Verify from PC-A1:  ping 10.2.2.10
    Verify from PC-B1:  ping 10.1.1.10

    Credentials: cisco / cisco  (console and alpine SSH/login)
    See labs/bgp-redundant/README.md for addressing, protocol design, and failover tests.
  title: BGP iBGP OSPF Redundant
  version: 0.1.0
links:
{links_yaml()}
nodes:
{nodes}"""

    cfg_dir = Path(__file__).with_name("configs")
    cfg_dir.mkdir(exist_ok=True)
    for name, content in [
        ("CE-A.txt", CE_A),
        ("CE-B.txt", CE_B),
        ("PE1.txt", PE1),
        ("PE2.txt", PE2),
        ("P.txt", P),
        ("PC-A1.sh", "hostname PC-A1\nip addr add 10.1.1.10/24 dev eth0\nip link set dev eth0 up\nip route add default via 10.1.1.1\n"),
        ("PC-A2.sh", "hostname PC-A2\nip addr add 10.1.1.11/24 dev eth0\nip link set dev eth0 up\nip route add default via 10.1.1.1\n"),
        ("PC-B1.sh", "hostname PC-B1\nip addr add 10.2.2.10/24 dev eth0\nip link set dev eth0 up\nip route add default via 10.2.2.1\n"),
        ("PC-B2.sh", "hostname PC-B2\nip addr add 10.2.2.11/24 dev eth0\nip link set dev eth0 up\nip route add default via 10.2.2.1\n"),
    ]:
        (cfg_dir / name).write_text(content.strip("\n") + "\n", encoding="utf-8")

    OUT.write_text(lab, encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
    print(f"wrote configs to {cfg_dir}")


if __name__ == "__main__":
    main()
