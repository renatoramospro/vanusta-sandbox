#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucftkub-89c6n4====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucftkub-89c6n4 exit=${code}====="
exit "$code"
