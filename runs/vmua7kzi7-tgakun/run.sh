#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua7kzi7-tgakun====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua7kzi7-tgakun exit=${code}====="
exit "$code"
