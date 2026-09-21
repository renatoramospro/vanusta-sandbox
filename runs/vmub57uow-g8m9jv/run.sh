#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmub57uow-g8m9jv====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmub57uow-g8m9jv exit=${code}====="
exit "$code"
