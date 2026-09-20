#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9oxqui-ze0b5b====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9oxqui-ze0b5b exit=${code}====="
exit "$code"
