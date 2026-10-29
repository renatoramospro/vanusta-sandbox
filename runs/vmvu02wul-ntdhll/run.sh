#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvu02wul-ntdhll====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvu02wul-ntdhll exit=${code}====="
exit "$code"
