#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcmjsrr-sam1ga====="
(
  set -e
  python 'forward_chaining.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcmjsrr-sam1ga exit=${code}====="
exit "$code"
