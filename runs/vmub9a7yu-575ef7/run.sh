#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmub9a7yu-575ef7====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmub9a7yu-575ef7 exit=${code}====="
exit "$code"
