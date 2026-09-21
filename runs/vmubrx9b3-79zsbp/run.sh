#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubrx9b3-79zsbp====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubrx9b3-79zsbp exit=${code}====="
exit "$code"
