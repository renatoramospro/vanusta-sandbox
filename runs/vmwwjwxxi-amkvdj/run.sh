#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwwjwxxi-amkvdj====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwwjwxxi-amkvdj exit=${code}====="
exit "$code"
