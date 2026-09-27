#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuj9nw46-lyzfjz====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuj9nw46-lyzfjz exit=${code}====="
exit "$code"
