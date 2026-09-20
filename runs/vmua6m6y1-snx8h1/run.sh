#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua6m6y1-snx8h1====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua6m6y1-snx8h1 exit=${code}====="
exit "$code"
