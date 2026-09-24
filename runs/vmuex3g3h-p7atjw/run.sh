#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuex3g3h-p7atjw====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuex3g3h-p7atjw exit=${code}====="
exit "$code"
