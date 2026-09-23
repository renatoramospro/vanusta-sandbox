#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmue5k5fy-s211ar====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmue5k5fy-s211ar exit=${code}====="
exit "$code"
