#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmue1h3bc-jy3kta====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmue1h3bc-jy3kta exit=${code}====="
exit "$code"
