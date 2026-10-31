#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvwgtd1r-m4x156====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvwgtd1r-m4x156 exit=${code}====="
exit "$code"
