#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuko8wz0-ijcxx0====="
(
  set -e
  python 'sharding_demo.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuko8wz0-ijcxx0 exit=${code}====="
exit "$code"
