#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmug4ph3q-mrt0ta====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmug4ph3q-mrt0ta exit=${code}====="
exit "$code"
