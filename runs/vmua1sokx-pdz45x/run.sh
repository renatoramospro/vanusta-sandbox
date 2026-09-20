#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua1sokx-pdz45x====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua1sokx-pdz45x exit=${code}====="
exit "$code"
