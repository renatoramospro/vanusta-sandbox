#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwyh4p1d-fgpecx====="
(
  set -e
  python 'gpu_manager.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwyh4p1d-fgpecx exit=${code}====="
exit "$code"
