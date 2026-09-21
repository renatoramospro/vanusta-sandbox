#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubtupvs-tiw4bz====="
(
  set -e
  python 'failover_experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubtupvs-tiw4bz exit=${code}====="
exit "$code"
