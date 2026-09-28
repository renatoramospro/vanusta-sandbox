#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukyr0gr-2bx1yb====="
(
  set -e
  python 'circuit_breaker.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukyr0gr-2bx1yb exit=${code}====="
exit "$code"
