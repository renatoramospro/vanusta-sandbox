#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucjohxz-bvcukl====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucjohxz-bvcukl exit=${code}====="
exit "$code"
