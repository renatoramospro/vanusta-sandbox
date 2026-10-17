#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcbq3l4-0ewty6====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcbq3l4-0ewty6 exit=${code}====="
exit "$code"
