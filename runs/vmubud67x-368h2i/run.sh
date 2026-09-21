#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubud67x-368h2i====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubud67x-368h2i exit=${code}====="
exit "$code"
