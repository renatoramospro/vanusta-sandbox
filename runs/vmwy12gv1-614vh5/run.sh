#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwy12gv1-614vh5====="
(
  set -e
  python 'actor_simulation.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwy12gv1-614vh5 exit=${code}====="
exit "$code"
