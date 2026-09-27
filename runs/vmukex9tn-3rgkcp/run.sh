#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukex9tn-3rgkcp====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukex9tn-3rgkcp exit=${code}====="
exit "$code"
