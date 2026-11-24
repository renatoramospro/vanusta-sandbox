#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwu7vmad-pjc17a====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwu7vmad-pjc17a exit=${code}====="
exit "$code"
