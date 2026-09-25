#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuh2sasj-xj3aan====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuh2sasj-xj3aan exit=${code}====="
exit "$code"
