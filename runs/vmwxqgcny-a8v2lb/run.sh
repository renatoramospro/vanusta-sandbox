#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxqgcny-a8v2lb====="
(
  set -e
  python 'simulator.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxqgcny-a8v2lb exit=${code}====="
exit "$code"
