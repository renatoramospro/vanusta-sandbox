#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwycez88-w89dtk====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwycez88-w89dtk exit=${code}====="
exit "$code"
