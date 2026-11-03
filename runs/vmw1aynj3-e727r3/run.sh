#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmw1aynj3-e727r3====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmw1aynj3-e727r3 exit=${code}====="
exit "$code"
