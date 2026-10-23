#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvljma4y-7a8wjw====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvljma4y-7a8wjw exit=${code}====="
exit "$code"
