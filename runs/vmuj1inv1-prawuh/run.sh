#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuj1inv1-prawuh====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuj1inv1-prawuh exit=${code}====="
exit "$code"
