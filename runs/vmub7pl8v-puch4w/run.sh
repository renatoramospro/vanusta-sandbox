#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmub7pl8v-puch4w====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmub7pl8v-puch4w exit=${code}====="
exit "$code"
