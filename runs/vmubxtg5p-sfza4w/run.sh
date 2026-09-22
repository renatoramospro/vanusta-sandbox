#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubxtg5p-sfza4w====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubxtg5p-sfza4w exit=${code}====="
exit "$code"
