#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwsnxr1t-vlsxfn====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwsnxr1t-vlsxfn exit=${code}====="
exit "$code"
