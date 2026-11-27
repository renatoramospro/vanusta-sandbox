#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwygt331-4ovv2b====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwygt331-4ovv2b exit=${code}====="
exit "$code"
