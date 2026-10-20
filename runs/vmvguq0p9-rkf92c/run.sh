#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvguq0p9-rkf92c====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvguq0p9-rkf92c exit=${code}====="
exit "$code"
