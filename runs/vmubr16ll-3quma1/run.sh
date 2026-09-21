#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubr16ll-3quma1====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubr16ll-3quma1 exit=${code}====="
exit "$code"
