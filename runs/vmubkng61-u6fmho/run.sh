#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubkng61-u6fmho====="
(
  set -e
  python 'cache_system.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubkng61-u6fmho exit=${code}====="
exit "$code"
