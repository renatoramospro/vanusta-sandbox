#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmul73wsk-c307f2====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmul73wsk-c307f2 exit=${code}====="
exit "$code"
