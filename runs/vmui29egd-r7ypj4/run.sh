#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmui29egd-r7ypj4====="
(
  set -e
  python 'lzw.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmui29egd-r7ypj4 exit=${code}====="
exit "$code"
