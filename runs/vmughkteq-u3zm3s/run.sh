#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmughkteq-u3zm3s====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmughkteq-u3zm3s exit=${code}====="
exit "$code"
