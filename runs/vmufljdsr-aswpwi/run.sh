#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmufljdsr-aswpwi====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmufljdsr-aswpwi exit=${code}====="
exit "$code"
