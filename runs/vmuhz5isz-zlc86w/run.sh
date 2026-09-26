#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhz5isz-zlc86w====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhz5isz-zlc86w exit=${code}====="
exit "$code"
