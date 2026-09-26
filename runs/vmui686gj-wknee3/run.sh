#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmui686gj-wknee3====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmui686gj-wknee3 exit=${code}====="
exit "$code"
