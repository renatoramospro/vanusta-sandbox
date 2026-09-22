#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmud11kzl-4lwvd5====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmud11kzl-4lwvd5 exit=${code}====="
exit "$code"
