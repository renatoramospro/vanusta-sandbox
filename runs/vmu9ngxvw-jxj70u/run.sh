#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9ngxvw-jxj70u====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9ngxvw-jxj70u exit=${code}====="
exit "$code"
