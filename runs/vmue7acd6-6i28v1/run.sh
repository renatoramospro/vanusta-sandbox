#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmue7acd6-6i28v1====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmue7acd6-6i28v1 exit=${code}====="
exit "$code"
