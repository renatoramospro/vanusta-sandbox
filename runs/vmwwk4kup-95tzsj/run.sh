#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwwk4kup-95tzsj====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwwk4kup-95tzsj exit=${code}====="
exit "$code"
