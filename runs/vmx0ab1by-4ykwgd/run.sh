#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmx0ab1by-4ykwgd====="
(
  set -e
  python 'simulator.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmx0ab1by-4ykwgd exit=${code}====="
exit "$code"
