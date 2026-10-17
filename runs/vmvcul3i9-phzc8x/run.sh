#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcul3i9-phzc8x====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcul3i9-phzc8x exit=${code}====="
exit "$code"
