#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmx01ae0h-hd11hn====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmx01ae0h-hd11hn exit=${code}====="
exit "$code"
