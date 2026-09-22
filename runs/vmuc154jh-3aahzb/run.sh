#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuc154jh-3aahzb====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuc154jh-3aahzb exit=${code}====="
exit "$code"
