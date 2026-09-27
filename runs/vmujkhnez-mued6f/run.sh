#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujkhnez-mued6f====="
(
  set -e
  python 'experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujkhnez-mued6f exit=${code}====="
exit "$code"
