#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9ij7bd-pf43sp====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9ij7bd-pf43sp exit=${code}====="
exit "$code"
