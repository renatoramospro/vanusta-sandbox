#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwyl3h1z-484jbf====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwyl3h1z-484jbf exit=${code}====="
exit "$code"
