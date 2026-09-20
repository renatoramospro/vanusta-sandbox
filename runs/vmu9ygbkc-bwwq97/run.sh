#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9ygbkc-bwwq97====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9ygbkc-bwwq97 exit=${code}====="
exit "$code"
