#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua0zhjy-oxt6fk====="
(
  set -e
  python 'federated_leak_detection.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua0zhjy-oxt6fk exit=${code}====="
exit "$code"
