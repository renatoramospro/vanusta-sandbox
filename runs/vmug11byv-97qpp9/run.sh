#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmug11byv-97qpp9====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmug11byv-97qpp9 exit=${code}====="
exit "$code"
