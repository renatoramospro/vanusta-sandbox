#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua30v4t-1cggys====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua30v4t-1cggys exit=${code}====="
exit "$code"
