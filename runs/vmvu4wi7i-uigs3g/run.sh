#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvu4wi7i-uigs3g====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvu4wi7i-uigs3g exit=${code}====="
exit "$code"
