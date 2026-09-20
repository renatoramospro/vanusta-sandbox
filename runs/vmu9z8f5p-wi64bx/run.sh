#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9z8f5p-wi64bx====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9z8f5p-wi64bx exit=${code}====="
exit "$code"
