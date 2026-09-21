#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubw3osb-bqr65d====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubw3osb-bqr65d exit=${code}====="
exit "$code"
