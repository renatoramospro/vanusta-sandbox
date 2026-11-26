#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxjhmsb-lmepaq====="
(
  set -e
  python 'tracing_experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxjhmsb-lmepaq exit=${code}====="
exit "$code"
