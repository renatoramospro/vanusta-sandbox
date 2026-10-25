#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvo5hwwz-3agvdo====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvo5hwwz-3agvdo exit=${code}====="
exit "$code"
