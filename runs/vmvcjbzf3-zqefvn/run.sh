#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcjbzf3-zqefvn====="
(
  set -e
  python 'kernel.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcjbzf3-zqefvn exit=${code}====="
exit "$code"
