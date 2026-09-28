#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmul4bpvd-h7fpo4====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmul4bpvd-h7fpo4 exit=${code}====="
exit "$code"
