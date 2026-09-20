#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9tqni5-u1fldt====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9tqni5-u1fldt exit=${code}====="
exit "$code"
