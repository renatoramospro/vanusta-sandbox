#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvgz47hw-12os8a====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvgz47hw-12os8a exit=${code}====="
exit "$code"
