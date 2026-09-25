#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuh9zllz-q9qrt8====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuh9zllz-q9qrt8 exit=${code}====="
exit "$code"
