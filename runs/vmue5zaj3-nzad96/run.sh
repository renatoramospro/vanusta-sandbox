#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmue5zaj3-nzad96====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmue5zaj3-nzad96 exit=${code}====="
exit "$code"
