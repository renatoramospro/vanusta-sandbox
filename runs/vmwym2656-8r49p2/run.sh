#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwym2656-8r49p2====="
(
  set -e
  python 'experiment_energy.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwym2656-8r49p2 exit=${code}====="
exit "$code"
