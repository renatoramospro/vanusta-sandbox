#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwy03pff-joofsr====="
(
  set -e
  python 'actor_simulation.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwy03pff-joofsr exit=${code}====="
exit "$code"
