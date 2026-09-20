#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuafx1q3-e72ru0====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuafx1q3-e72ru0 exit=${code}====="
exit "$code"
