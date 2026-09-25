#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmug9qu89-h42nck====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmug9qu89-h42nck exit=${code}====="
exit "$code"
