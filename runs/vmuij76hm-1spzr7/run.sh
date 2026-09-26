#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuij76hm-1spzr7====="
(
  set -e
  python 'smtp_experiment_v3.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuij76hm-1spzr7 exit=${code}====="
exit "$code"
