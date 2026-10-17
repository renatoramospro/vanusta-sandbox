#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvc9wj41-6x42lm====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvc9wj41-6x42lm exit=${code}====="
exit "$code"
