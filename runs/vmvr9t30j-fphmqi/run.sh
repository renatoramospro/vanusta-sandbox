#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvr9t30j-fphmqi====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvr9t30j-fphmqi exit=${code}====="
exit "$code"
