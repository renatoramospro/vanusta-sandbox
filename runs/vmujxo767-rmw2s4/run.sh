#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujxo767-rmw2s4====="
(
  set -e
  python 'bplus_tree.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujxo767-rmw2s4 exit=${code}====="
exit "$code"
