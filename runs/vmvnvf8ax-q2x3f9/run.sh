#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvnvf8ax-q2x3f9====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvnvf8ax-q2x3f9 exit=${code}====="
exit "$code"
