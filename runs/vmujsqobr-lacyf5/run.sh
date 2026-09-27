#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujsqobr-lacyf5====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujsqobr-lacyf5 exit=${code}====="
exit "$code"
