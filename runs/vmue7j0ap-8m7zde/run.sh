#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmue7j0ap-8m7zde====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmue7j0ap-8m7zde exit=${code}====="
exit "$code"
