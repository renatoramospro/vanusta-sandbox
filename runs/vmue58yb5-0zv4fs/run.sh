#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmue58yb5-0zv4fs====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmue58yb5-0zv4fs exit=${code}====="
exit "$code"
