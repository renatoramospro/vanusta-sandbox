#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubsffqg-z5bimt====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubsffqg-z5bimt exit=${code}====="
exit "$code"
