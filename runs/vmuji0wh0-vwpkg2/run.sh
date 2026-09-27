#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuji0wh0-vwpkg2====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuji0wh0-vwpkg2 exit=${code}====="
exit "$code"
