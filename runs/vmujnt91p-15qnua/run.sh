#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujnt91p-15qnua====="
(
  set -e
  python 'quadtree_secure_validated.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujnt91p-15qnua exit=${code}====="
exit "$code"
