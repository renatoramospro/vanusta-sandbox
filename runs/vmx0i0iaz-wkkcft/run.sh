#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmx0i0iaz-wkkcft====="
(
  set -e
  python 'rate_limiter.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmx0i0iaz-wkkcft exit=${code}====="
exit "$code"
