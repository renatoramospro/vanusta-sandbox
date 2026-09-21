#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmub8iyxw-r3ddih====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmub8iyxw-r3ddih exit=${code}====="
exit "$code"
