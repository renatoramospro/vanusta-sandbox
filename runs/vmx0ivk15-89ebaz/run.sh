#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmx0ivk15-89ebaz====="
(
  set -e
  python 'rate_limiter.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmx0ivk15-89ebaz exit=${code}====="
exit "$code"
