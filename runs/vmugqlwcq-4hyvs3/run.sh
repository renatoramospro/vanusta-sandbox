#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmugqlwcq-4hyvs3====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmugqlwcq-4hyvs3 exit=${code}====="
exit "$code"
