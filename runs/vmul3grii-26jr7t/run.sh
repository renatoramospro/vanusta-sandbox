#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmul3grii-26jr7t====="
(
  set -e
  python 'simulator.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmul3grii-26jr7t exit=${code}====="
exit "$code"
