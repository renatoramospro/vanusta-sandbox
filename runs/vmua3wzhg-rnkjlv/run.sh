#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua3wzhg-rnkjlv====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua3wzhg-rnkjlv exit=${code}====="
exit "$code"
