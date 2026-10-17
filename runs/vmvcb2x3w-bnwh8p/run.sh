#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcb2x3w-bnwh8p====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcb2x3w-bnwh8p exit=${code}====="
exit "$code"
