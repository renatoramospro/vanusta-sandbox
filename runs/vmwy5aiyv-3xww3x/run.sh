#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwy5aiyv-3xww3x====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwy5aiyv-3xww3x exit=${code}====="
exit "$code"
