#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmx0lrq48-kqz6ww====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmx0lrq48-kqz6ww exit=${code}====="
exit "$code"
