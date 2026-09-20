#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9kyglh-uaipt4====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9kyglh-uaipt4 exit=${code}====="
exit "$code"
