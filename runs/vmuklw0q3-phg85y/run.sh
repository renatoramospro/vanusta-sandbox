#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuklw0q3-phg85y====="
(
  set -e
  python 'experiment_secure.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuklw0q3-phg85y exit=${code}====="
exit "$code"
