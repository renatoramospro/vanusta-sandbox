#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwvj51co-qz9yc1====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwvj51co-qz9yc1 exit=${code}====="
exit "$code"
