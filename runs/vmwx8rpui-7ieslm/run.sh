#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwx8rpui-7ieslm====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwx8rpui-7ieslm exit=${code}====="
exit "$code"
