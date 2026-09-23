#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmudxmbq9-um0jos====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmudxmbq9-um0jos exit=${code}====="
exit "$code"
