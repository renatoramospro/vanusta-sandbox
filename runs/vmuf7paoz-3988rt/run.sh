#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuf7paoz-3988rt====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuf7paoz-3988rt exit=${code}====="
exit "$code"
