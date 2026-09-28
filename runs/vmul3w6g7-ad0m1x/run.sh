#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmul3w6g7-ad0m1x====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmul3w6g7-ad0m1x exit=${code}====="
exit "$code"
