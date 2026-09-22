#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucazypc-bg6ful====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucazypc-bg6ful exit=${code}====="
exit "$code"
