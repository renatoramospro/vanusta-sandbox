#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuf4pq6p-9zb36g====="
(
  set -e
  python 'health_check_system.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuf4pq6p-9zb36g exit=${code}====="
exit "$code"
