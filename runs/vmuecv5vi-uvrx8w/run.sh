#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuecv5vi-uvrx8w====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuecv5vi-uvrx8w exit=${code}====="
exit "$code"
