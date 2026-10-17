#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcwu43n-pdj0q0====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcwu43n-pdj0q0 exit=${code}====="
exit "$code"
