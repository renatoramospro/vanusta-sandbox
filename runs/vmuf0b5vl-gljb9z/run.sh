#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuf0b5vl-gljb9z====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuf0b5vl-gljb9z exit=${code}====="
exit "$code"
