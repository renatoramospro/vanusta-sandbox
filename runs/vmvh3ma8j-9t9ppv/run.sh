#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvh3ma8j-9t9ppv====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvh3ma8j-9t9ppv exit=${code}====="
exit "$code"
