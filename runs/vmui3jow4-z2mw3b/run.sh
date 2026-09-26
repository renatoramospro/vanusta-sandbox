#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmui3jow4-z2mw3b====="
(
  set -e
  python 'circuit_breaker.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmui3jow4-z2mw3b exit=${code}====="
exit "$code"
