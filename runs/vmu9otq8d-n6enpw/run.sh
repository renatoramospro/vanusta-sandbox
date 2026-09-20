#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9otq8d-n6enpw====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9otq8d-n6enpw exit=${code}====="
exit "$code"
