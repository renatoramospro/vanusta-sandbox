#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukb68nk-dephoh====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukb68nk-dephoh exit=${code}====="
exit "$code"
