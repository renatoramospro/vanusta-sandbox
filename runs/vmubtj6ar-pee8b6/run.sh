#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubtj6ar-pee8b6====="
(
  set -e
  python 'failover_experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubtj6ar-pee8b6 exit=${code}====="
exit "$code"
