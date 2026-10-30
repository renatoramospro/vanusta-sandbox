#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvvfmmgt-0kh0ow====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvvfmmgt-0kh0ow exit=${code}====="
exit "$code"
