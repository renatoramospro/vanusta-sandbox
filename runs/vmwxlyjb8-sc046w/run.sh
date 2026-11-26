#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxlyjb8-sc046w====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxlyjb8-sc046w exit=${code}====="
exit "$code"
