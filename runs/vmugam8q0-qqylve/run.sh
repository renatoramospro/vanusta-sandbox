#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmugam8q0-qqylve====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmugam8q0-qqylve exit=${code}====="
exit "$code"
