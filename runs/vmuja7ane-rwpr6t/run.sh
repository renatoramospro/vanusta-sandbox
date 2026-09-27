#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuja7ane-rwpr6t====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuja7ane-rwpr6t exit=${code}====="
exit "$code"
