#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuitl9u6-kdicks====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuitl9u6-kdicks exit=${code}====="
exit "$code"
