#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubsj6lc-rcb30t====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubsj6lc-rcb30t exit=${code}====="
exit "$code"
