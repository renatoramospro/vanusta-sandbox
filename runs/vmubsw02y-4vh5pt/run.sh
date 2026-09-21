#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubsw02y-4vh5pt====="
(
  set -e
  python 'orchestrator_sim.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubsw02y-4vh5pt exit=${code}====="
exit "$code"
