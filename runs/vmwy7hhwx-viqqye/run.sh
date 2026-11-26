#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwy7hhwx-viqqye====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwy7hhwx-viqqye exit=${code}====="
exit "$code"
