#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwt5ikpp-s3er6s====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwt5ikpp-s3er6s exit=${code}====="
exit "$code"
