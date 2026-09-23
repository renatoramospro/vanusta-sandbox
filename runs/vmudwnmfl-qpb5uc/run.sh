#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmudwnmfl-qpb5uc====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmudwnmfl-qpb5uc exit=${code}====="
exit "$code"
