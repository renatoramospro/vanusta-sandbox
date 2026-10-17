#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcten82-y94h1u====="
(
  set -e
  python 'vcs_system.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcten82-y94h1u exit=${code}====="
exit "$code"
