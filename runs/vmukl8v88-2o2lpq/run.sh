#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukl8v88-2o2lpq====="
(
  set -e
  python 'experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukl8v88-2o2lpq exit=${code}====="
exit "$code"
