#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuehnn58-kly3nf====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuehnn58-kly3nf exit=${code}====="
exit "$code"
