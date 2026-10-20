#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvgkyx9e-zrvxj2====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvgkyx9e-zrvxj2 exit=${code}====="
exit "$code"
