#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvqm4gwv-taidmj====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvqm4gwv-taidmj exit=${code}====="
exit "$code"
