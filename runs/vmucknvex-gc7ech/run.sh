#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucknvex-gc7ech====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucknvex-gc7ech exit=${code}====="
exit "$code"
