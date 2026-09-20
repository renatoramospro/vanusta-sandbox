#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9gp4cb-2cket4====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9gp4cb-2cket4 exit=${code}====="
exit "$code"
