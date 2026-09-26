#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmui6nlsk-1tatbm====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmui6nlsk-1tatbm exit=${code}====="
exit "$code"
