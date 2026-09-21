#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuaihjrd-tyqpad====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuaihjrd-tyqpad exit=${code}====="
exit "$code"
