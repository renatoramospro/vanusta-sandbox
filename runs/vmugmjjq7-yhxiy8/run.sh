#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmugmjjq7-yhxiy8====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmugmjjq7-yhxiy8 exit=${code}====="
exit "$code"
