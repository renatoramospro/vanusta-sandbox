#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua0x1tv-23r4nm====="
(
  set -e
  python 'federated_leak_detection.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua0x1tv-23r4nm exit=${code}====="
exit "$code"
