#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9oal6g-5pzbc5====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9oal6g-5pzbc5 exit=${code}====="
exit "$code"
