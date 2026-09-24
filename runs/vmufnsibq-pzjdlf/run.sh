#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmufnsibq-pzjdlf====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmufnsibq-pzjdlf exit=${code}====="
exit "$code"
