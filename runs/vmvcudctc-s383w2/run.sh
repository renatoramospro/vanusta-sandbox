#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcudctc-s383w2====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcudctc-s383w2 exit=${code}====="
exit "$code"
