#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwt149dm-kc5a3w====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwt149dm-kc5a3w exit=${code}====="
exit "$code"
