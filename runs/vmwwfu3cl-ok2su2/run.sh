#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwwfu3cl-ok2su2====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwwfu3cl-ok2su2 exit=${code}====="
exit "$code"
