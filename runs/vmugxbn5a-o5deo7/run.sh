#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmugxbn5a-o5deo7====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmugxbn5a-o5deo7 exit=${code}====="
exit "$code"
