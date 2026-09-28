#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukjqxba-5rssjz====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukjqxba-5rssjz exit=${code}====="
exit "$code"
