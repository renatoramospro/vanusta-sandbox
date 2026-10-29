#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvtlm3t7-a12xh2====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvtlm3t7-a12xh2 exit=${code}====="
exit "$code"
