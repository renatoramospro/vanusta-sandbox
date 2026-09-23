#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmue3q975-6k5wp6====="
(
  set -e
  python 'generate_docs.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmue3q975-6k5wp6 exit=${code}====="
exit "$code"
