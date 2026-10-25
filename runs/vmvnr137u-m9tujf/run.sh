#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvnr137u-m9tujf====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvnr137u-m9tujf exit=${code}====="
exit "$code"
