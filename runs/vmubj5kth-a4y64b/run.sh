#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubj5kth-a4y64b====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubj5kth-a4y64b exit=${code}====="
exit "$code"
