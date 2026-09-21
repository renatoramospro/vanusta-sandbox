#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuajrnt3-cp17u4====="
(
  set -e
  python 'persistence_system.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuajrnt3-cp17u4 exit=${code}====="
exit "$code"
