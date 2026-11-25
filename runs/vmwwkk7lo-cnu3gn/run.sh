#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwwkk7lo-cnu3gn====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwwkk7lo-cnu3gn exit=${code}====="
exit "$code"
