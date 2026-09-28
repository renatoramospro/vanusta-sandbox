#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukyyph3-m179qv====="
(
  set -e
  python 'circuit_breaker.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukyyph3-m179qv exit=${code}====="
exit "$code"
