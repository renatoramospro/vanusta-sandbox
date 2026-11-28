#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwzqs5n1-cperi7====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwzqs5n1-cperi7 exit=${code}====="
exit "$code"
