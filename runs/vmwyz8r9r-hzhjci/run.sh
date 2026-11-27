#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwyz8r9r-hzhjci====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwyz8r9r-hzhjci exit=${code}====="
exit "$code"
