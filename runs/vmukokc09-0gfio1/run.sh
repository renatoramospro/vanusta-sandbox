#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukokc09-0gfio1====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukokc09-0gfio1 exit=${code}====="
exit "$code"
