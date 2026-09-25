#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmugmq9bz-qfh4tx====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmugmq9bz-qfh4tx exit=${code}====="
exit "$code"
