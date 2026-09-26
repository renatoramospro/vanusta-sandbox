#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuii4gua-crmaoz====="
(
  set -e
  python 'smtp_experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuii4gua-crmaoz exit=${code}====="
exit "$code"
