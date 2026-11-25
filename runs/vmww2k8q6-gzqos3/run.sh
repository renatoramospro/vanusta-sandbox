#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmww2k8q6-gzqos3====="
(
  set -e
  python 'raft_simulator_corrected.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmww2k8q6-gzqos3 exit=${code}====="
exit "$code"
