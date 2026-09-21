#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuawc5er-hrynan====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuawc5er-hrynan exit=${code}====="
exit "$code"
