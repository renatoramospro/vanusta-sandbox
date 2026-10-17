#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvd1ns6k-slrr8r====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvd1ns6k-slrr8r exit=${code}====="
exit "$code"
