#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubvw0qz-idi43r====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubvw0qz-idi43r exit=${code}====="
exit "$code"
