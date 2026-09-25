#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuh98bzw-3ba9k2====="
(
  set -e
  python 'vm.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuh98bzw-3ba9k2 exit=${code}====="
exit "$code"
