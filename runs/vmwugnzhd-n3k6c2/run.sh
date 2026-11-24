#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwugnzhd-n3k6c2====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwugnzhd-n3k6c2 exit=${code}====="
exit "$code"
