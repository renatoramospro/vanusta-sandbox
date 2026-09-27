#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujndr3f-nuky0o====="
(
  set -e
  python 'quadtree_fixed.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujndr3f-nuky0o exit=${code}====="
exit "$code"
