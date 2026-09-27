#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuj8p23q-wdr4m6====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuj8p23q-wdr4m6 exit=${code}====="
exit "$code"
