#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmueo78c3-10czzk====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmueo78c3-10czzk exit=${code}====="
exit "$code"
