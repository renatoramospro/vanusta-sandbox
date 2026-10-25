#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvo9w2d5-gpy8ks====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvo9w2d5-gpy8ks exit=${code}====="
exit "$code"
