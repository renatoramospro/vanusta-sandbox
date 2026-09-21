#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmub0ezew-nz6ww1====="
(
  set -e
  python 'goap_system.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmub0ezew-nz6ww1 exit=${code}====="
exit "$code"
