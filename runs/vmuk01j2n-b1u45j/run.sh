#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuk01j2n-b1u45j====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuk01j2n-b1u45j exit=${code}====="
exit "$code"
