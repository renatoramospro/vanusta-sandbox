#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9qgwg9-tltgf0====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9qgwg9-tltgf0 exit=${code}====="
exit "$code"
