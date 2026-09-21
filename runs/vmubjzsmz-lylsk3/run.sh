#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubjzsmz-lylsk3====="
(
  set -e
  python 'rate_limiter.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubjzsmz-lylsk3 exit=${code}====="
exit "$code"
