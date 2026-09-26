#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmui0fvj4-7m3ax1====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmui0fvj4-7m3ax1 exit=${code}====="
exit "$code"
