#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmublhsbx-q7y8k5====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmublhsbx-q7y8k5 exit=${code}====="
exit "$code"
