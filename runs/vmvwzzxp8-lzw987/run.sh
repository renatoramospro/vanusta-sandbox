#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvwzzxp8-lzw987====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvwzzxp8-lzw987 exit=${code}====="
exit "$code"
