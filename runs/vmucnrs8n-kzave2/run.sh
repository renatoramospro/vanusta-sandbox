#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucnrs8n-kzave2====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucnrs8n-kzave2 exit=${code}====="
exit "$code"
