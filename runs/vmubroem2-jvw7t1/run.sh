#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubroem2-jvw7t1====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubroem2-jvw7t1 exit=${code}====="
exit "$code"
