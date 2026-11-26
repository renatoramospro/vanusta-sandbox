#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxoyiwk-xnyoc4====="
(
  set -e
  python 'simulation.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxoyiwk-xnyoc4 exit=${code}====="
exit "$code"
