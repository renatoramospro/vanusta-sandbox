#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua6fj3x-e07ava====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua6fj3x-e07ava exit=${code}====="
exit "$code"
