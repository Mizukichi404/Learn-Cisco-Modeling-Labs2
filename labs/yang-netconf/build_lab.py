#!/usr/bin/env python3
"""Generate the CML2 importable YAML for the YANG / NETCONF / RESTCONF lab."""

from pathlib import Path

OUT = Path(__file__).with_name("yang-netconf-restconf.yaml")

XE_COMMON = """
no ip domain lookup
ip domain name lab.local
!
aaa new-model
!
aaa authentication login default local
aaa authorization exec default local
!
enable secret cisco
username cisco privilege 15 secret cisco
!
service timestamps debug datetime msec
service timestamps log datetime msec
!
ip cef
!
crypto key generate rsa general-keys modulus 2048
!
ip ssh version 2
!
netconf-yang
restconf
ip http authentication local
ip http server
ip http secure-server
!
"""

XE_LINES = """
!
line con 0
 exec-timeout 0 0
 logging synchronous
line vty 0 4
 login local
 transport input ssh
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
{extra_lines} no shutdown
!
"""


def indent(text, n):
    pad = " " * n
    return "\n".join(pad + line if line else pad for line in text.splitlines())


def csr_node(nid, label, x, y, config, n_phys):
    """CSR1000v / IOS-XE style node. Physical ports map to GigabitEthernet1..N.

    Unlike IOSv exports, CML csr1000v node definitions expose only physical
    GigabitEthernet ports (Gi1 = i0). Loopback0 exists only in the IOS config.
    """
    ifaces = []
    for slot in range(n_phys):
        ifaces.append(
            f"    - id: i{slot}\n"
            f"      label: GigabitEthernet{slot + 1}\n"
            f"      slot: {slot}\n"
            f"      type: physical"
        )
    cfg = indent(config.strip("\n") + "\n", 6)
    iface_yaml = "\n".join(ifaces)
    return f"""  - boot_disk_size: 0
    configuration: |-
{cfg}
    cpu_limit: 100
    cpus: 2
    data_volume: 0
    hide_links: false
    id: {nid}
    image_definition: null
    label: {label}
    node_definition: csr1000v
    ram: 3072
    tags: []
    x: {x}
    y: {y}
    interfaces:
{iface_yaml}
"""


def alpine_node(nid, label, x, y, hostname, ip, gw=None):
    routes = ""
    if gw:
        routes = f"ip route add default via {gw}\n"
    config = f"""# this is a shell script which will be sourced at boot
hostname {hostname}
USERNAME=cisco
PASSWORD=cisco
ip addr add {ip} dev eth0
ip link set dev eth0 up
{routes}# Optional tools when the node has package/network access:
#   apk add --no-cache curl python3 py3-pip openssh-client
#   pip3 install ncclient requests
# Client examples live in labs/yang-netconf/scripts/ on the GitHub repo.
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
    ram: 512
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


OSPF_P2P = """ ip ospf network point-to-point
 ip ospf hello-interval 5
 ip ospf dead-interval 20
"""

R1 = f"""!
hostname R1
!
{XE_COMMON}
interface Loopback0
 description YANG-lab RID R1
 ip address 1.1.1.1 255.255.255.255
!
{iface("GigabitEthernet1", "MGMT LAN to SW-MGMT / MGMT-PC", "172.16.0.1 255.255.255.0")}
{iface("GigabitEthernet2", "OSPF to R2", "10.0.12.1 255.255.255.252", OSPF_P2P)}
router ospf 1
 router-id 1.1.1.1
 passive-interface default
 no passive-interface GigabitEthernet2
 network 1.1.1.1 0.0.0.0 area 0
 network 10.0.12.0 0.0.0.3 area 0
!
{XE_LINES}
"""

R2 = f"""!
hostname R2
!
{XE_COMMON}
interface Loopback0
 description YANG-lab RID R2
 ip address 2.2.2.2 255.255.255.255
!
{iface("GigabitEthernet1", "MGMT LAN to SW-MGMT / MGMT-PC", "172.16.0.2 255.255.255.0")}
{iface("GigabitEthernet2", "OSPF to R1", "10.0.12.2 255.255.255.252", OSPF_P2P)}
router ospf 1
 router-id 2.2.2.2
 passive-interface default
 no passive-interface GigabitEthernet2
 network 2.2.2.2 0.0.0.0 area 0
 network 10.0.12.0 0.0.0.3 area 0
!
{XE_LINES}
"""

LINKS = [
    # R1/R2: i0=Gi1 (mgmt), i1=Gi2 (OSPF). SW-MGMT / MGMT-PC use their physical ports.
    ("l0", "n0", "n2", "i0", "i0", "R1-GigabitEthernet1<->SW-MGMT-port0"),
    ("l1", "n1", "n2", "i0", "i1", "R2-GigabitEthernet1<->SW-MGMT-port1"),
    ("l2", "n3", "n2", "i0", "i2", "MGMT-PC-eth0<->SW-MGMT-port2"),
    ("l3", "n0", "n1", "i1", "i1", "R1-GigabitEthernet2<->R2-GigabitEthernet2"),
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
            csr_node("n0", "R1", -200, -40, R1, 2),
            csr_node("n1", "R2", 200, -40, R2, 2),
            ums_node("n2", "SW-MGMT", 0, 160, "ums-yang-mgmt-01"),
            alpine_node(
                "n3",
                "MGMT-PC",
                0,
                320,
                "MGMT-PC",
                "172.16.0.10/24",
            ),
        ]
    )

    lab = f"""lab:
  description: YANG learning lab with NETCONF and RESTCONF on two IOS-XE (CSR1000v)
    routers, OSPF between them, and an Alpine management PC on a shared management LAN.
  notes: |
    Import this file in CML2 (Lab Manager > Import). Start all nodes and wait
    until OSPF is FULL and YANG processes are running on R1/R2.

    MGMT LAN 172.16.0.0/24:
      R1 172.16.0.1  R2 172.16.0.2  MGMT-PC 172.16.0.10

    NETCONF TCP/830  RESTCONF HTTPS/443  SSH TCP/22
    Credentials: cisco / cisco

    Docs (EN + JA): labs/yang-netconf/README.md
    Client scripts: labs/yang-netconf/scripts/
  title: YANG NETCONF RESTCONF Lab
  version: 0.1.0
links:
{links_yaml()}
nodes:
{nodes}"""

    cfg_dir = Path(__file__).with_name("configs")
    cfg_dir.mkdir(exist_ok=True)
    for name, content in [
        ("R1.txt", R1),
        ("R2.txt", R2),
        (
            "MGMT-PC.sh",
            "hostname MGMT-PC\n"
            "ip addr add 172.16.0.10/24 dev eth0\n"
            "ip link set dev eth0 up\n",
        ),
    ]:
        (cfg_dir / name).write_text(content.strip("\n") + "\n", encoding="utf-8")

    OUT.write_text(lab, encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
    print(f"wrote configs to {cfg_dir}")


if __name__ == "__main__":
    main()
