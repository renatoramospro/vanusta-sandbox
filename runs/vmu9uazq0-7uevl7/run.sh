#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9uazq0-7uevl7====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9uazq0-7uevl7 exit=${code}====="
exit "$code"
