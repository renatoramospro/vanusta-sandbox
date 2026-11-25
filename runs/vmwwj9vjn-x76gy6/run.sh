#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwwj9vjn-x76gy6====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwwj9vjn-x76gy6 exit=${code}====="
exit "$code"
