#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmul56icj-hp4qkn====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmul56icj-hp4qkn exit=${code}====="
exit "$code"
