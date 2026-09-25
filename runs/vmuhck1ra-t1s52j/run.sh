#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhck1ra-t1s52j====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhck1ra-t1s52j exit=${code}====="
exit "$code"
