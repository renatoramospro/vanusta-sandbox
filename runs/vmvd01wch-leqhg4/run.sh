#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvd01wch-leqhg4====="
(
  set -e
  python 'oidc_experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvd01wch-leqhg4 exit=${code}====="
exit "$code"
