#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwycqnow-b3e10d====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwycqnow-b3e10d exit=${code}====="
exit "$code"
