#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuggijhi-sm1kyc====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuggijhi-sm1kyc exit=${code}====="
exit "$code"
