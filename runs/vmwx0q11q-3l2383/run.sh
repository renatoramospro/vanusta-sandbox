#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwx0q11q-3l2383====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwx0q11q-3l2383 exit=${code}====="
exit "$code"
