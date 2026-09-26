#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuidapx7-jtvuor====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuidapx7-jtvuor exit=${code}====="
exit "$code"
