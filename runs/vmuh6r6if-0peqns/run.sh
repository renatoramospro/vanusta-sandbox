#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuh6r6if-0peqns====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuh6r6if-0peqns exit=${code}====="
exit "$code"
