#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhi7yet-5bf471====="
(
  set -e
  python 'router_experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhi7yet-5bf471 exit=${code}====="
exit "$code"
