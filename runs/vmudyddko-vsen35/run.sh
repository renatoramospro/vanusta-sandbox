#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmudyddko-vsen35====="
(
  set -e
  python 'documenter_engine.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmudyddko-vsen35 exit=${code}====="
exit "$code"
