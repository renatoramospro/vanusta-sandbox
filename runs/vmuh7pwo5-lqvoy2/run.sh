#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuh7pwo5-lqvoy2====="
(
  set -e
  python 'merkle_tree.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuh7pwo5-lqvoy2 exit=${code}====="
exit "$code"
