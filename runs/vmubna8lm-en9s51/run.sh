#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubna8lm-en9s51====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubna8lm-en9s51 exit=${code}====="
exit "$code"
