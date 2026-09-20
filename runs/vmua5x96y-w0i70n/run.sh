#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua5x96y-w0i70n====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua5x96y-w0i70n exit=${code}====="
exit "$code"
