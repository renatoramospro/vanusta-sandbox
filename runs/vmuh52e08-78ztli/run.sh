#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuh52e08-78ztli====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuh52e08-78ztli exit=${code}====="
exit "$code"
