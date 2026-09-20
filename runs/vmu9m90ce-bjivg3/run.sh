#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9m90ce-bjivg3====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9m90ce-bjivg3 exit=${code}====="
exit "$code"
