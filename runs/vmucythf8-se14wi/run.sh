#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucythf8-se14wi====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucythf8-se14wi exit=${code}====="
exit "$code"
