#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuk13l7d-ptfo19====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuk13l7d-ptfo19 exit=${code}====="
exit "$code"
