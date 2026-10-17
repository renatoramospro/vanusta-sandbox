#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcpz5ad-kppenu====="
(
  set -e
  python 'experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcpz5ad-kppenu exit=${code}====="
exit "$code"
