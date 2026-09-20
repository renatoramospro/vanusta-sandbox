#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9o29wq-u0qulq====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9o29wq-u0qulq exit=${code}====="
exit "$code"
