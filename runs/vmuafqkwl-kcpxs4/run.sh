#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuafqkwl-kcpxs4====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuafqkwl-kcpxs4 exit=${code}====="
exit "$code"
