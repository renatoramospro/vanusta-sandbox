#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwyv9uvw-p9fqzw====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwyv9uvw-p9fqzw exit=${code}====="
exit "$code"
