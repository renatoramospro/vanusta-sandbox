#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmue2vez3-07j6fd====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmue2vez3-07j6fd exit=${code}====="
exit "$code"
