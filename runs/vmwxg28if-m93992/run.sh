#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxg28if-m93992====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxg28if-m93992 exit=${code}====="
exit "$code"
