#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuknhwf3-tqcczd====="
(
  set -e
  python 'sharding_demo.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuknhwf3-tqcczd exit=${code}====="
exit "$code"
