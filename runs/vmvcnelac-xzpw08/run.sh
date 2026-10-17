#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcnelac-xzpw08====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcnelac-xzpw08 exit=${code}====="
exit "$code"
