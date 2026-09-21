#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuaohgv3-hpuwje====="
(
  set -e
  python 'experiment_fixed.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuaohgv3-hpuwje exit=${code}====="
exit "$code"
