#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9io0r7-wddp1c====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9io0r7-wddp1c exit=${code}====="
exit "$code"
