#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwylqj1a-tnn313====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwylqj1a-tnn313 exit=${code}====="
exit "$code"
