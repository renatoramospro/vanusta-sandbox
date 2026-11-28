#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmx0hsy7r-vseu6j====="
(
  set -e
  python 'rate_limiter.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmx0hsy7r-vseu6j exit=${code}====="
exit "$code"
