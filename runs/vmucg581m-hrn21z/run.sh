#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucg581m-hrn21z====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucg581m-hrn21z exit=${code}====="
exit "$code"
