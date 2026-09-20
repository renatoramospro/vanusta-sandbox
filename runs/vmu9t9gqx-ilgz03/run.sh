#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9t9gqx-ilgz03====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9t9gqx-ilgz03 exit=${code}====="
exit "$code"
