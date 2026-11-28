#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmx0lzkc9-67x4n9====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmx0lzkc9-67x4n9 exit=${code}====="
exit "$code"
