#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukze54k-g73o8z====="
(
  set -e
  python 'circuit_breaker.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukze54k-g73o8z exit=${code}====="
exit "$code"
