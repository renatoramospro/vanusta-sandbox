#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvpg81fn-3t1dz9====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvpg81fn-3t1dz9 exit=${code}====="
exit "$code"
