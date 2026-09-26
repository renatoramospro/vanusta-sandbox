#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhord3y-tt3qp3====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhord3y-tt3qp3 exit=${code}====="
exit "$code"
