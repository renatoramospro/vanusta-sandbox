#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmx0k93af-6jnd18====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmx0k93af-6jnd18 exit=${code}====="
exit "$code"
