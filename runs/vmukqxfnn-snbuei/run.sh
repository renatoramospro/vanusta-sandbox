#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukqxfnn-snbuei====="
(
  set -e
  python 'experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukqxfnn-snbuei exit=${code}====="
exit "$code"
