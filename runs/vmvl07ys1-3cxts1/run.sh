#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvl07ys1-3cxts1====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvl07ys1-3cxts1 exit=${code}====="
exit "$code"
