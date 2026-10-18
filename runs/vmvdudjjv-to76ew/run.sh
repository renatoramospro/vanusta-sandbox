#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvdudjjv-to76ew====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvdudjjv-to76ew exit=${code}====="
exit "$code"
