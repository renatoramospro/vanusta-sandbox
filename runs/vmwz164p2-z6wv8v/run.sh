#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwz164p2-z6wv8v====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwz164p2-z6wv8v exit=${code}====="
exit "$code"
