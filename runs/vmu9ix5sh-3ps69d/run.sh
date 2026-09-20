#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9ix5sh-3ps69d====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9ix5sh-3ps69d exit=${code}====="
exit "$code"
