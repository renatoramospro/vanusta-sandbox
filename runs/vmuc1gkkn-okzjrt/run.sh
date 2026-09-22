#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuc1gkkn-okzjrt====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuc1gkkn-okzjrt exit=${code}====="
exit "$code"
