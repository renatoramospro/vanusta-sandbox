#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuk4ule4-l4qs5n====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuk4ule4-l4qs5n exit=${code}====="
exit "$code"
