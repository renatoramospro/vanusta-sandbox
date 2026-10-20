#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvgph03l-jrabzk====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvgph03l-jrabzk exit=${code}====="
exit "$code"
