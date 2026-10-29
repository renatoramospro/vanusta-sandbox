#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvth7wzg-e1x3bn====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvth7wzg-e1x3bn exit=${code}====="
exit "$code"
