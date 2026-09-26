#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuj0ro8h-e48ug0====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuj0ro8h-e48ug0 exit=${code}====="
exit "$code"
