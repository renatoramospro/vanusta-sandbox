#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmub85jff-zyuzba====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmub85jff-zyuzba exit=${code}====="
exit "$code"
