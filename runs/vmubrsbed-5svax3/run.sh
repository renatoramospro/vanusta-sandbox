#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubrsbed-5svax3====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubrsbed-5svax3 exit=${code}====="
exit "$code"
