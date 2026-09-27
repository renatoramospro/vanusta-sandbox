#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuk4n2dh-tutbho====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuk4n2dh-tutbho exit=${code}====="
exit "$code"
