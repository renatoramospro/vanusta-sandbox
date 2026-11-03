#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmw16cqnz-p7ql4s====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmw16cqnz-p7ql4s exit=${code}====="
exit "$code"
