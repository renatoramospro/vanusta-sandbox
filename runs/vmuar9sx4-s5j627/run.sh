#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuar9sx4-s5j627====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuar9sx4-s5j627 exit=${code}====="
exit "$code"
