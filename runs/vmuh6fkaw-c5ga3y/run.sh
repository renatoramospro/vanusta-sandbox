#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuh6fkaw-c5ga3y====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuh6fkaw-c5ga3y exit=${code}====="
exit "$code"
