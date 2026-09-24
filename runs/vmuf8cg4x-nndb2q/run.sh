#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuf8cg4x-nndb2q====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuf8cg4x-nndb2q exit=${code}====="
exit "$code"
