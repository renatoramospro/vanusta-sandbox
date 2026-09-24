#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmug0bbna-1rn1nz====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmug0bbna-1rn1nz exit=${code}====="
exit "$code"
