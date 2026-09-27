#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujn27qe-93b83i====="
(
  set -e
  python 'quadtree.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujn27qe-93b83i exit=${code}====="
exit "$code"
