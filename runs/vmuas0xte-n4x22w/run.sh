#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuas0xte-n4x22w====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuas0xte-n4x22w exit=${code}====="
exit "$code"
