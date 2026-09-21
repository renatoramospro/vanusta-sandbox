#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubodn0t-1gn9re====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubodn0t-1gn9re exit=${code}====="
exit "$code"
