#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwyghko5-b6vecn====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwyghko5-b6vecn exit=${code}====="
exit "$code"
