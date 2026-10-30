#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvv19nc4-h5gxsm====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvv19nc4-h5gxsm exit=${code}====="
exit "$code"
