#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuc2bj7o-1lc974====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuc2bj7o-1lc974 exit=${code}====="
exit "$code"
