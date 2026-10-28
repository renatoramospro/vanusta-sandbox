#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvspcvnu-ftrjof====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvspcvnu-ftrjof exit=${code}====="
exit "$code"
