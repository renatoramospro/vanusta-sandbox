#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmugqwn1k-u0cbw6====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmugqwn1k-u0cbw6 exit=${code}====="
exit "$code"
