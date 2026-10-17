#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvckq6ib-xulh8p====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvckq6ib-xulh8p exit=${code}====="
exit "$code"
