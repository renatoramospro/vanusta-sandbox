#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmul657yu-wi7q4c====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmul657yu-wi7q4c exit=${code}====="
exit "$code"
