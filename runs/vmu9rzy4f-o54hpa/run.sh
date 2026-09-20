#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9rzy4f-o54hpa====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9rzy4f-o54hpa exit=${code}====="
exit "$code"
