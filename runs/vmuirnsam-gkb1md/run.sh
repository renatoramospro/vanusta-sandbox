#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuirnsam-gkb1md====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuirnsam-gkb1md exit=${code}====="
exit "$code"
