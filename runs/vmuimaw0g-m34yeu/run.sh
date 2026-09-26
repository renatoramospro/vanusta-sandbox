#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuimaw0g-m34yeu====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuimaw0g-m34yeu exit=${code}====="
exit "$code"
