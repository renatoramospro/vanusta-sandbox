#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmww11ig4-lue6to====="
(
  set -e
  python 'raft_simulator.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmww11ig4-lue6to exit=${code}====="
exit "$code"
