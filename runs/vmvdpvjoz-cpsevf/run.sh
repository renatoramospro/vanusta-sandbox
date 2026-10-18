#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvdpvjoz-cpsevf====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvdpvjoz-cpsevf exit=${code}====="
exit "$code"
