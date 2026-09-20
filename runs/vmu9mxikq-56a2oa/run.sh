#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9mxikq-56a2oa====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9mxikq-56a2oa exit=${code}====="
exit "$code"
