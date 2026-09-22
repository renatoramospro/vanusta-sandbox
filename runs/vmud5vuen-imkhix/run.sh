#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmud5vuen-imkhix====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmud5vuen-imkhix exit=${code}====="
exit "$code"
