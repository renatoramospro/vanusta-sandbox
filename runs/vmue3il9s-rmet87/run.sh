#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmue3il9s-rmet87====="
(
  set -e
  python 'generate_docs.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmue3il9s-rmet87 exit=${code}====="
exit "$code"
