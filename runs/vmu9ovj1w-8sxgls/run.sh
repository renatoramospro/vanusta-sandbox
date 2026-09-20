#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9ovj1w-8sxgls====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9ovj1w-8sxgls exit=${code}====="
exit "$code"
