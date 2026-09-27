#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujz672c-ykmop1====="
(
  set -e
  python 'minhash_lsh.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujz672c-ykmop1 exit=${code}====="
exit "$code"
