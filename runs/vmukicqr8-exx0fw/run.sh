#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukicqr8-exx0fw====="
(
  set -e
  python 'strangler_experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukicqr8-exx0fw exit=${code}====="
exit "$code"
