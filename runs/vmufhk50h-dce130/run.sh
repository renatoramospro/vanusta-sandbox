#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmufhk50h-dce130====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmufhk50h-dce130 exit=${code}====="
exit "$code"
