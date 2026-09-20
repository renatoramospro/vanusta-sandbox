#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9niu9q-n8du53====="
(
  set -e
  python 'analyzer.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9niu9q-n8du53 exit=${code}====="
exit "$code"
