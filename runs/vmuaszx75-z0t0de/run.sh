#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuaszx75-z0t0de====="
(
  set -e
  python 'replay_system.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuaszx75-z0t0de exit=${code}====="
exit "$code"
