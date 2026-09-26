#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuilvg4t-kfr5bg====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuilvg4t-kfr5bg exit=${code}====="
exit "$code"
