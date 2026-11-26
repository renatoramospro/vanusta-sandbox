#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwwwk7jw-i4bu1o====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwwwk7jw-i4bu1o exit=${code}====="
exit "$code"
