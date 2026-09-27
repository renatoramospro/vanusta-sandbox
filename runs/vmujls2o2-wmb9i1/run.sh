#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujls2o2-wmb9i1====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujls2o2-wmb9i1 exit=${code}====="
exit "$code"
