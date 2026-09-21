#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubk4kjg-s8xw9c====="
(
  set -e
  python 'rate_limiter.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubk4kjg-s8xw9c exit=${code}====="
exit "$code"
