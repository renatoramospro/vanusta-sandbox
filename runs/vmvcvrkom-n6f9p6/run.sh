#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcvrkom-n6f9p6====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcvrkom-n6f9p6 exit=${code}====="
exit "$code"
