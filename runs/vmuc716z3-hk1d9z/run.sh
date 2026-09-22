#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuc716z3-hk1d9z====="
(
  set -e
  python 'framework_simulation.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuc716z3-hk1d9z exit=${code}====="
exit "$code"
