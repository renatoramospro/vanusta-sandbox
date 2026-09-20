#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuacpu6m-mfven9====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuacpu6m-mfven9 exit=${code}====="
exit "$code"
