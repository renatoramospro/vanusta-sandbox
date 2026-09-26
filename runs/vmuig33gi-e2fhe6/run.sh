#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuig33gi-e2fhe6====="
(
  set -e
  python 'di_container.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuig33gi-e2fhe6 exit=${code}====="
exit "$code"
