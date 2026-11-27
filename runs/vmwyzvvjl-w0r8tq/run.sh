#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwyzvvjl-w0r8tq====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwyzvvjl-w0r8tq exit=${code}====="
exit "$code"
