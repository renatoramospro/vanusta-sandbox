#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmww2ziqb-jb49oj====="
(
  set -e
  python 'raft_simulator_final.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmww2ziqb-jb49oj exit=${code}====="
exit "$code"
