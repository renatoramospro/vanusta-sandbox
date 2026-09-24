#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmufmt6m7-ql2fvb====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmufmt6m7-ql2fvb exit=${code}====="
exit "$code"
