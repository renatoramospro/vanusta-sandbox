#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua3enfq-gi7li9====="
(
  set -e
  python 'distributed_lock_experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua3enfq-gi7li9 exit=${code}====="
exit "$code"
