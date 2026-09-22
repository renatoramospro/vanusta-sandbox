#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucggr3n-xnquzs====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucggr3n-xnquzs exit=${code}====="
exit "$code"
