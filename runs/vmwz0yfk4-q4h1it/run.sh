#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwz0yfk4-q4h1it====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwz0yfk4-q4h1it exit=${code}====="
exit "$code"
