#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmugu9521-ugmsfz====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmugu9521-ugmsfz exit=${code}====="
exit "$code"
