#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmul5tr25-wyyhsc====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmul5tr25-wyyhsc exit=${code}====="
exit "$code"
