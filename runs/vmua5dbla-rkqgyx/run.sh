#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua5dbla-rkqgyx====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua5dbla-rkqgyx exit=${code}====="
exit "$code"
