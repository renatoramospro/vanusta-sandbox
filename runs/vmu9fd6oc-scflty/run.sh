#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9fd6oc-scflty====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9fd6oc-scflty exit=${code}====="
exit "$code"
