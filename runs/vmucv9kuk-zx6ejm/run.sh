#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucv9kuk-zx6ejm====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucv9kuk-zx6ejm exit=${code}====="
exit "$code"
