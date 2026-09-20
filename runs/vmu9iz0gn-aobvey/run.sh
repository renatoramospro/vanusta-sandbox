#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9iz0gn-aobvey====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9iz0gn-aobvey exit=${code}====="
exit "$code"
