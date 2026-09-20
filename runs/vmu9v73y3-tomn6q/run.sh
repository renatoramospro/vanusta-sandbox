#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9v73y3-tomn6q====="
(
  set -e
  python 'container.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9v73y3-tomn6q exit=${code}====="
exit "$code"
