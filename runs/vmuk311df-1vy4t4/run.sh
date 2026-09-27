#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuk311df-1vy4t4====="
(
  set -e
  python 'mvcc_engine.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuk311df-1vy4t4 exit=${code}====="
exit "$code"
