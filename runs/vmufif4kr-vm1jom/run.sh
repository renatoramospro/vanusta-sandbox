#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmufif4kr-vm1jom====="
(
  set -e
  python 'feature_flags_corrected.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmufif4kr-vm1jom exit=${code}====="
exit "$code"
