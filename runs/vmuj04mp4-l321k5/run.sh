#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuj04mp4-l321k5====="
(
  set -e
  python 'interpreter.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuj04mp4-l321k5 exit=${code}====="
exit "$code"
