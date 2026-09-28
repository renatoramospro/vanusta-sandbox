#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmul6itvo-u58859====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmul6itvo-u58859 exit=${code}====="
exit "$code"
