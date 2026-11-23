#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwsjjrnl-6e9cby====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwsjjrnl-6e9cby exit=${code}====="
exit "$code"
