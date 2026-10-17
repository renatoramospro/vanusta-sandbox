#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcdv8tq-5oys6w====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcdv8tq-5oys6w exit=${code}====="
exit "$code"
