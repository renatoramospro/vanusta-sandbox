#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9u2u97-hzw5ro====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9u2u97-hzw5ro exit=${code}====="
exit "$code"
