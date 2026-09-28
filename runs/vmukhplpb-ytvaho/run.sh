#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukhplpb-ytvaho====="
(
  set -e
  python 'secure_experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukhplpb-ytvaho exit=${code}====="
exit "$code"
