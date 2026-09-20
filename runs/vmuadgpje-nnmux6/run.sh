#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuadgpje-nnmux6====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuadgpje-nnmux6 exit=${code}====="
exit "$code"
