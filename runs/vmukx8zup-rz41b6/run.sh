#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukx8zup-rz41b6====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukx8zup-rz41b6 exit=${code}====="
exit "$code"
