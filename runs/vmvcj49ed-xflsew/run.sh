#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcj49ed-xflsew====="
(
  set -e
  python 'kernel.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcj49ed-xflsew exit=${code}====="
exit "$code"
