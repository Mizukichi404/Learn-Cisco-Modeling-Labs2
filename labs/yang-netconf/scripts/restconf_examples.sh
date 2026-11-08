#!/usr/bin/env bash
# RESTCONF examples for the CML2 YANG lab (R1 = 172.16.0.1).
# Requires: curl, and a host that can reach the management LAN.
#
# Usage:
#   export R1=172.16.0.1
#   export AUTH=cisco:cisco
#   ./restconf_examples.sh

set -euo pipefail

R1="${R1:-172.16.0.1}"
AUTH="${AUTH:-cisco:cisco}"
BASE="https://${R1}/restconf"

CURL=(curl -k -sS -u "$AUTH" -H "Accept: application/yang-data+json")

echo "=== 1) RESTCONF root (YANG library entry points) ==="
"${CURL[@]}" "$BASE/" | head -c 2000
echo
echo

echo "=== 2) Native interface list (Cisco-IOS-XE-interfaces-oper) ==="
"${CURL[@]}" \
  "$BASE/data/Cisco-IOS-XE-interfaces-oper:interfaces" | head -c 4000
echo
echo

echo "=== 3) Loopback0 description (ietf-interfaces style path may vary by image) ==="
"${CURL[@]}" \
  "$BASE/data/Cisco-IOS-XE-native:native/interface/Loopback=0" | head -c 4000
echo
echo

echo "=== 4) PATCH Loopback0 description via native model ==="
"${CURL[@]}" -X PATCH \
  -H "Content-Type: application/yang-data+json" \
  -d '{"Cisco-IOS-XE-native:Loopback":[{"name":0,"description":"updated-via-RESTCONF"}]}' \
  "$BASE/data/Cisco-IOS-XE-native:native/interface/Loopback=0"
echo "(empty body on success is normal)"
echo

echo "=== 5) Re-read Loopback0 ==="
"${CURL[@]}" \
  "$BASE/data/Cisco-IOS-XE-native:native/interface/Loopback=0" | head -c 4000
echo
