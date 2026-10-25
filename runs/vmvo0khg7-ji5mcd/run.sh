#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvo0khg7-ji5mcd====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvo0khg7-ji5mcd exit=${code}====="
exit "$code"
