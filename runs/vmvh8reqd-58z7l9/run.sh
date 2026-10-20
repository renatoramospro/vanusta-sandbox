#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvh8reqd-58z7l9====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvh8reqd-58z7l9 exit=${code}====="
exit "$code"
