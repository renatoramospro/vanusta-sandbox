#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9fd27m-hnmpwe====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9fd27m-hnmpwe exit=${code}====="
exit "$code"
