#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmudwfy7s-pw81h8====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmudwfy7s-pw81h8 exit=${code}====="
exit "$code"
