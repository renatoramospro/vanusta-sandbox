#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmufkctd8-qj9g84====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmufkctd8-qj9g84 exit=${code}====="
exit "$code"
