#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhejkhh-n12049====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhejkhh-n12049 exit=${code}====="
exit "$code"
