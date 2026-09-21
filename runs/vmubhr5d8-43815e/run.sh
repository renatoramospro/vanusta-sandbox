#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubhr5d8-43815e====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubhr5d8-43815e exit=${code}====="
exit "$code"
