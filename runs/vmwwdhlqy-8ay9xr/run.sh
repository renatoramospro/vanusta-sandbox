#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwwdhlqy-8ay9xr====="
(
  set -e
  python 'pathfinder.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwwdhlqy-8ay9xr exit=${code}====="
exit "$code"
