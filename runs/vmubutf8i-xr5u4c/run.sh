#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubutf8i-xr5u4c====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubutf8i-xr5u4c exit=${code}====="
exit "$code"
