#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubogqor-gxi1le====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubogqor-gxi1le exit=${code}====="
exit "$code"
