#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujxwr5j-kb56dx====="
(
  set -e
  python 'bplus_tree.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujxwr5j-kb56dx exit=${code}====="
exit "$code"
