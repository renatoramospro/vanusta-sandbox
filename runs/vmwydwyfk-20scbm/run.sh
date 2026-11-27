#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwydwyfk-20scbm====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwydwyfk-20scbm exit=${code}====="
exit "$code"
