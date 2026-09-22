#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuc3hwei-fm1gw9====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuc3hwei-fm1gw9 exit=${code}====="
exit "$code"
