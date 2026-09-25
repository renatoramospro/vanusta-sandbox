#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhb1cvp-4x945y====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhb1cvp-4x945y exit=${code}====="
exit "$code"
