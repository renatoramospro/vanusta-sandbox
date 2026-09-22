#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucvxany-osjj1a====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucvxany-osjj1a exit=${code}====="
exit "$code"
