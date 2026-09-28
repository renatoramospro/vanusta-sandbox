#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukzxf09-t1ef7r====="
(
  set -e
  python 'experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukzxf09-t1ef7r exit=${code}====="
exit "$code"
