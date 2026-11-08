#!/usr/bin/env python3
"""NETCONF <get-config> example for the CML2 YANG lab.

Requires:
  pip install ncclient

Usage:
  python3 netconf_get_config.py
  python3 netconf_get_config.py --host 172.16.0.2 --filter interfaces
"""

from __future__ import annotations

import argparse
import sys

try:
    from ncclient import manager
except ImportError:
    sys.stderr.write(
        "ncclient is not installed. Run:  pip install ncclient\n"
    )
    sys.exit(1)


INTERFACE_FILTER = """
<filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
    <interface/>
  </native>
</filter>
""".strip()

OSPF_FILTER = """
<filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
    <router>
      <ospf xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-ospf"/>
    </router>
  </native>
</filter>
""".strip()

FILTERS = {
    "running": None,
    "interfaces": INTERFACE_FILTER,
    "ospf": OSPF_FILTER,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="172.16.0.1", help="NETCONF host")
    parser.add_argument("--port", type=int, default=830)
    parser.add_argument("--username", default="cisco")
    parser.add_argument("--password", default="cisco")
    parser.add_argument(
        "--filter",
        choices=sorted(FILTERS),
        default="interfaces",
        help="Which subtree to retrieve",
    )
    args = parser.parse_args()

    filter_xml = FILTERS[args.filter]
    with manager.connect(
        host=args.host,
        port=args.port,
        username=args.username,
        password=args.password,
        hostkey_verify=False,
        device_params={"name": "csr"},
        allow_agent=False,
        look_for_keys=False,
    ) as conn:
        print(f"# connected to {args.host}:{args.port}")
        print(f"# server capabilities (sample): {len(conn.server_capabilities)} total")
        for cap in list(conn.server_capabilities)[:8]:
            print(f"#   {cap}")
        print("# --- get-config ---")
        if filter_xml is None:
            result = conn.get_config(source="running")
        else:
            result = conn.get_config(source="running", filter=filter_xml)
        print(result.xml)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
