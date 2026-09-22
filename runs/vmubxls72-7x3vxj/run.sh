#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubxls72-7x3vxj====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubxls72-7x3vxj exit=${code}====="
exit "$code"
