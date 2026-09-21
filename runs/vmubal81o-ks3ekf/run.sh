#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubal81o-ks3ekf====="
(
  set -e
  python 'matchmaking_sim.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubal81o-ks3ekf exit=${code}====="
exit "$code"
