#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmugnsqvf-d555dl====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmugnsqvf-d555dl exit=${code}====="
exit "$code"
