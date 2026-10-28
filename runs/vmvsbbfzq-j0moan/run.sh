#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvsbbfzq-j0moan====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvsbbfzq-j0moan exit=${code}====="
exit "$code"
