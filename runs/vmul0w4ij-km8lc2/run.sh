#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmul0w4ij-km8lc2====="
(
  set -e
  python 'experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmul0w4ij-km8lc2 exit=${code}====="
exit "$code"
