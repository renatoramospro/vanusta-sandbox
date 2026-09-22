#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucdgo0l-519yhb====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucdgo0l-519yhb exit=${code}====="
exit "$code"
