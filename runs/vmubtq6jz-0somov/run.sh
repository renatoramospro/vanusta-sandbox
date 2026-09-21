#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubtq6jz-0somov====="
(
  set -e
  python 'failover_experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubtq6jz-0somov exit=${code}====="
exit "$code"
