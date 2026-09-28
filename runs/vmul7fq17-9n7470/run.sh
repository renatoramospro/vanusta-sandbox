#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmul7fq17-9n7470====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmul7fq17-9n7470 exit=${code}====="
exit "$code"
