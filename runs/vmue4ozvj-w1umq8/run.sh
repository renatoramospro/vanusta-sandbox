#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmue4ozvj-w1umq8====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmue4ozvj-w1umq8 exit=${code}====="
exit "$code"
