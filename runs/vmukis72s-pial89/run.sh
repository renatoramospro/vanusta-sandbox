#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukis72s-pial89====="
(
  set -e
  python 'strangler_secure_experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukis72s-pial89 exit=${code}====="
exit "$code"
