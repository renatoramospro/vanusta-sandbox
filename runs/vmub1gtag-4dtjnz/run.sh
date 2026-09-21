#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmub1gtag-4dtjnz====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmub1gtag-4dtjnz exit=${code}====="
exit "$code"
