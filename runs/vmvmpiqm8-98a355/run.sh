#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvmpiqm8-98a355====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvmpiqm8-98a355 exit=${code}====="
exit "$code"
