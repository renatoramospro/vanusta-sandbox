#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmx05w56g-m8jlfg====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmx05w56g-m8jlfg exit=${code}====="
exit "$code"
