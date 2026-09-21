#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubs3r9c-ubgzhp====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubs3r9c-ubgzhp exit=${code}====="
exit "$code"
