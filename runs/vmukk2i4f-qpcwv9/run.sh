#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukk2i4f-qpcwv9====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukk2i4f-qpcwv9 exit=${code}====="
exit "$code"
