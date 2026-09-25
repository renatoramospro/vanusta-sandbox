#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhhwgre-8kiqq7====="
(
  set -e
  python 'router_experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhhwgre-8kiqq7 exit=${code}====="
exit "$code"
