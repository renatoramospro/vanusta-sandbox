#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuiqp3h4-85oal2====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuiqp3h4-85oal2 exit=${code}====="
exit "$code"
