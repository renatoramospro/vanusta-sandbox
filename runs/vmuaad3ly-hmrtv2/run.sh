#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuaad3ly-hmrtv2====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuaad3ly-hmrtv2 exit=${code}====="
exit "$code"
