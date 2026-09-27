#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuka7kk9-60h814====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuka7kk9-60h814 exit=${code}====="
exit "$code"
