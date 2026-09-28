#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmul0grvm-vcroia====="
(
  set -e
  python 'experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmul0grvm-vcroia exit=${code}====="
exit "$code"
