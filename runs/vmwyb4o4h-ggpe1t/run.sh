#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwyb4o4h-ggpe1t====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwyb4o4h-ggpe1t exit=${code}====="
exit "$code"
