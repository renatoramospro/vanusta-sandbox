#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmx0esoge-gf1b2d====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmx0esoge-gf1b2d exit=${code}====="
exit "$code"
