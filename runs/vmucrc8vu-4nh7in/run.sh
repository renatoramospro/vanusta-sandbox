#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucrc8vu-4nh7in====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucrc8vu-4nh7in exit=${code}====="
exit "$code"
