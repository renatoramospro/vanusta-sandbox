#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubfe2qj-lpuc26====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubfe2qj-lpuc26 exit=${code}====="
exit "$code"
