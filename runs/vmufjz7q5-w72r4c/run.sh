#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmufjz7q5-w72r4c====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmufjz7q5-w72r4c exit=${code}====="
exit "$code"
