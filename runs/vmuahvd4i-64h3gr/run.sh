#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuahvd4i-64h3gr====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuahvd4i-64h3gr exit=${code}====="
exit "$code"
