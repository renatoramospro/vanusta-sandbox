#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucasgt7-1k86ed====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucasgt7-1k86ed exit=${code}====="
exit "$code"
