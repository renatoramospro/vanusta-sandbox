#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmub4vve6-8eddp0====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmub4vve6-8eddp0 exit=${code}====="
exit "$code"
