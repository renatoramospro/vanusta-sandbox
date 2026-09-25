#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmugxq9x7-wug1oo====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmugxq9x7-wug1oo exit=${code}====="
exit "$code"
