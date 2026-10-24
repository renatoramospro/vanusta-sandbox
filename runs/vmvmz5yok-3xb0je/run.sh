#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvmz5yok-3xb0je====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvmz5yok-3xb0je exit=${code}====="
exit "$code"
