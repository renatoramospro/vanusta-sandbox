#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuk9zvi1-js01om====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuk9zvi1-js01om exit=${code}====="
exit "$code"
