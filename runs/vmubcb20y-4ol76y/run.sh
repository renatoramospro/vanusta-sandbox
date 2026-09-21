#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubcb20y-4ol76y====="
(
  set -e
  python 'streaming_sim.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubcb20y-4ol76y exit=${code}====="
exit "$code"
