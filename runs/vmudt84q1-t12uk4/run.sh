#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmudt84q1-t12uk4====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmudt84q1-t12uk4 exit=${code}====="
exit "$code"
