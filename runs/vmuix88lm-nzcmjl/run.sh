#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuix88lm-nzcmjl====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuix88lm-nzcmjl exit=${code}====="
exit "$code"
