#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmui3rdo5-wiwnxt====="
(
  set -e
  python 'circuit_breaker.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmui3rdo5-wiwnxt exit=${code}====="
exit "$code"
