#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9tb60t-o9uht7====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9tb60t-o9uht7 exit=${code}====="
exit "$code"
