#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuktlufm-z2a9b1====="
(
  set -e
  python 'experiment_eda_secure.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuktlufm-z2a9b1 exit=${code}====="
exit "$code"
