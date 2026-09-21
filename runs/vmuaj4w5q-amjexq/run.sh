#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuaj4w5q-amjexq====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuaj4w5q-amjexq exit=${code}====="
exit "$code"
