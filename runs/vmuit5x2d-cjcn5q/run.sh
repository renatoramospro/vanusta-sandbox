#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuit5x2d-cjcn5q====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuit5x2d-cjcn5q exit=${code}====="
exit "$code"
