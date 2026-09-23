#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmue1stvf-q5o9qx====="
(
  set -e
  python 'infracost_simulator.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmue1stvf-q5o9qx exit=${code}====="
exit "$code"
