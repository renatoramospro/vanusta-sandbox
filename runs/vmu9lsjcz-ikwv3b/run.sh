#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9lsjcz-ikwv3b====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9lsjcz-ikwv3b exit=${code}====="
exit "$code"
