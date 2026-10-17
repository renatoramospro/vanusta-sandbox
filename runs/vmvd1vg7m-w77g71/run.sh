#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvd1vg7m-w77g71====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvd1vg7m-w77g71 exit=${code}====="
exit "$code"
