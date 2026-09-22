#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucej9ms-p0x8eb====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucej9ms-p0x8eb exit=${code}====="
exit "$code"
