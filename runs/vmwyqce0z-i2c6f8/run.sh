#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwyqce0z-i2c6f8====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwyqce0z-i2c6f8 exit=${code}====="
exit "$code"
