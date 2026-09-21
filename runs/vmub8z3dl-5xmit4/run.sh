#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmub8z3dl-5xmit4====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmub8z3dl-5xmit4 exit=${code}====="
exit "$code"
