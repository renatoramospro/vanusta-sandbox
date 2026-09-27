#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuk2a2cl-3f8e0g====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuk2a2cl-3f8e0g exit=${code}====="
exit "$code"
