#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwzwcrfv-l5wb32====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwzwcrfv-l5wb32 exit=${code}====="
exit "$code"
