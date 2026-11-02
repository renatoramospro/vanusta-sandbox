#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvz7eq7m-ln74kb====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvz7eq7m-ln74kb exit=${code}====="
exit "$code"
