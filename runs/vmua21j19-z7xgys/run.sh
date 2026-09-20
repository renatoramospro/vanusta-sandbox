#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua21j19-z7xgys====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua21j19-z7xgys exit=${code}====="
exit "$code"
