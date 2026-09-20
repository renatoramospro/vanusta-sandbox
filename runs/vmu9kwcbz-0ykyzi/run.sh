#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9kwcbz-0ykyzi====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9kwcbz-0ykyzi exit=${code}====="
exit "$code"
