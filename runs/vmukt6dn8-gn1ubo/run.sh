#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukt6dn8-gn1ubo====="
(
  set -e
  python 'experiment_eda.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukt6dn8-gn1ubo exit=${code}====="
exit "$code"
