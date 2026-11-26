#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwx5bxr4-px6yxb====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwx5bxr4-px6yxb exit=${code}====="
exit "$code"
