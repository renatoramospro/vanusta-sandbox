#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuajks23-s3vyt0====="
(
  set -e
  python 'persistence_system.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuajks23-s3vyt0 exit=${code}====="
exit "$code"
