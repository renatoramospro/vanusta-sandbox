#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukjfbh5-z4mkec====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukjfbh5-z4mkec exit=${code}====="
exit "$code"
