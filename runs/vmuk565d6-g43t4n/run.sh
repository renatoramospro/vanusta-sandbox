#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuk565d6-g43t4n====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuk565d6-g43t4n exit=${code}====="
exit "$code"
