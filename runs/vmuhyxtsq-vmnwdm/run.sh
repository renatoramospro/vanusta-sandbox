#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhyxtsq-vmnwdm====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhyxtsq-vmnwdm exit=${code}====="
exit "$code"
