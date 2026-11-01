#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvyb5hbq-fpx93j====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvyb5hbq-fpx93j exit=${code}====="
exit "$code"
