#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmx0kp9gg-1jriae====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmx0kp9gg-1jriae exit=${code}====="
exit "$code"
