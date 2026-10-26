#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvpl1n1z-05x6ur====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvpl1n1z-05x6ur exit=${code}====="
exit "$code"
