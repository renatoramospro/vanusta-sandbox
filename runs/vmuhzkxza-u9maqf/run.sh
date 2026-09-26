#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhzkxza-u9maqf====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhzkxza-u9maqf exit=${code}====="
exit "$code"
