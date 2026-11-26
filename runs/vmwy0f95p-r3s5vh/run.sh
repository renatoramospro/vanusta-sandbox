#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwy0f95p-r3s5vh====="
(
  set -e
  python 'actor_simulation.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwy0f95p-r3s5vh exit=${code}====="
exit "$code"
