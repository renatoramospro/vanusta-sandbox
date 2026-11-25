#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmww5vu7e-kvsv3d====="
(
  set -e
  python 'raft_simulator_final.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmww5vu7e-kvsv3d exit=${code}====="
exit "$code"
