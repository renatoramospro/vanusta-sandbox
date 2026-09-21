#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubbmtli-uc54zs====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubbmtli-uc54zs exit=${code}====="
exit "$code"
