#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwssbwbd-aff8v4====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwssbwbd-aff8v4 exit=${code}====="
exit "$code"
