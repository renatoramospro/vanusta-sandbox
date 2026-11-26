#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxoqrff-krzvts====="
(
  set -e
  python 'simulation.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxoqrff-krzvts exit=${code}====="
exit "$code"
