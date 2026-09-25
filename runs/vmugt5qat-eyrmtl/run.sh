#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmugt5qat-eyrmtl====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmugt5qat-eyrmtl exit=${code}====="
exit "$code"
