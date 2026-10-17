#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcoh2gi-bkm64h====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcoh2gi-bkm64h exit=${code}====="
exit "$code"
