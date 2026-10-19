#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvff6h8m-r11jtw====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvff6h8m-r11jtw exit=${code}====="
exit "$code"
