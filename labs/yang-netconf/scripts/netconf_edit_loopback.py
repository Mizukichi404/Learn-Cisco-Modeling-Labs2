#!/usr/bin/env python3
"""NETCONF <edit-config> example: change Loopback0 description on R1/R2.

Requires:
  pip install ncclient

Usage:
  python3 netconf_edit_loopback.py --description "learned-via-NETCONF"
"""

from __future__ import annotations

import argparse
import sys

try:
    from ncclient import manager
    from ncclient.operations import RPCError
except ImportError:
    sys.stderr.write(
        "ncclient is not installed. Run:  pip install ncclient\n"
    )
    sys.exit(1)


EDIT_TEMPLATE = """
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
    <interface>
      <Loopback>
        <name>0</name>
        <description>{description}</description>
      </Loopback>
    </interface>
  </native>
</config>
""".strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="172.16.0.1")
    parser.add_argument("--port", type=int, default=830)
    parser.add_argument("--username", default="cisco")
    parser.add_argument("--password", default="cisco")
    parser.add_argument(
        "--description",
        default="updated-via-NETCONF",
        help="New Loopback0 description",
    )
    args = parser.parse_args()

    config = EDIT_TEMPLATE.format(description=args.description)

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
        print(f"# edit-config on {args.host} Loopback0 description={args.description!r}")
        try:
            reply = conn.edit_config(target="running", config=config)
        except RPCError as exc:
            sys.stderr.write(f"RPCError: {exc}\n")
            return 1
        print(reply)

        result = conn.get_config(
            source="running",
            filter="""
            <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
              <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
                <interface>
                  <Loopback>
                    <name>0</name>
                  </Loopback>
                </interface>
              </native>
            </filter>
            """.strip(),
        )
        print("# --- Loopback0 after edit ---")
        print(result.xml)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
