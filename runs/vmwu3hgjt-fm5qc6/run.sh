#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwu3hgjt-fm5qc6====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwu3hgjt-fm5qc6 exit=${code}====="
exit "$code"
