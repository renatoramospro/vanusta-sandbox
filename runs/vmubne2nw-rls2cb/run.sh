#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubne2nw-rls2cb====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubne2nw-rls2cb exit=${code}====="
exit "$code"
