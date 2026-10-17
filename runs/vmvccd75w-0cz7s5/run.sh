#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvccd75w-0cz7s5====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvccd75w-0cz7s5 exit=${code}====="
exit "$code"
