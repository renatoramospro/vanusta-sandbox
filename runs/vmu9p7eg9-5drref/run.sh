#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9p7eg9-5drref====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9p7eg9-5drref exit=${code}====="
exit "$code"
