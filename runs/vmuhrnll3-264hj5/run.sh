#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhrnll3-264hj5====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhrnll3-264hj5 exit=${code}====="
exit "$code"
