#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucjw7x6-69010d====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucjw7x6-69010d exit=${code}====="
exit "$code"
