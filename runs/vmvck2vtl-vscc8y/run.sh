#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvck2vtl-vscc8y====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvck2vtl-vscc8y exit=${code}====="
exit "$code"
