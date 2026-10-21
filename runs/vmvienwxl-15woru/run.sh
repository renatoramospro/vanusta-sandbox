#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvienwxl-15woru====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvienwxl-15woru exit=${code}====="
exit "$code"
