#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmue2jwcg-7qmtwi====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmue2jwcg-7qmtwi exit=${code}====="
exit "$code"
