#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwvnj772-olph7a====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwvnj772-olph7a exit=${code}====="
exit "$code"
