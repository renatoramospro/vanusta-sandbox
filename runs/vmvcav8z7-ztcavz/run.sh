#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcav8z7-ztcavz====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcav8z7-ztcavz exit=${code}====="
exit "$code"
