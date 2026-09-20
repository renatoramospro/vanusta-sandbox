#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua4how3-7ieac7====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua4how3-7ieac7 exit=${code}====="
exit "$code"
