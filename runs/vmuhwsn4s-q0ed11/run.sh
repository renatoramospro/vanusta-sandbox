#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhwsn4s-q0ed11====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhwsn4s-q0ed11 exit=${code}====="
exit "$code"
