#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuh604or-q7x0kx====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuh604or-q7x0kx exit=${code}====="
exit "$code"
