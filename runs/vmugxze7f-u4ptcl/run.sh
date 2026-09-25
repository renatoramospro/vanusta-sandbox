#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmugxze7f-u4ptcl====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmugxze7f-u4ptcl exit=${code}====="
exit "$code"
