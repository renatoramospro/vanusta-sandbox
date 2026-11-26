#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwx9f0ns-sir6sf====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwx9f0ns-sir6sf exit=${code}====="
exit "$code"
