#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuilnst9-kmhgnm====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuilnst9-kmhgnm exit=${code}====="
exit "$code"
