#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubj592t-h64d19====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubj592t-h64d19 exit=${code}====="
exit "$code"
