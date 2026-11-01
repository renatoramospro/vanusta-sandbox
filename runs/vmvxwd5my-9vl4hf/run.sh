#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvxwd5my-9vl4hf====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvxwd5my-9vl4hf exit=${code}====="
exit "$code"
