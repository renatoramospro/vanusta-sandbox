#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9oawx4-lxcka8====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9oawx4-lxcka8 exit=${code}====="
exit "$code"
