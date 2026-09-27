#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuj2sur4-x4tud9====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuj2sur4-x4tud9 exit=${code}====="
exit "$code"
