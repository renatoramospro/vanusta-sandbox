#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubow9ju-ltd85e====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubow9ju-ltd85e exit=${code}====="
exit "$code"
