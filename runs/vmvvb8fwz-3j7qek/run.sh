#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvvb8fwz-3j7qek====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvvb8fwz-3j7qek exit=${code}====="
exit "$code"
