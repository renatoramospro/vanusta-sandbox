#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuc6tm18-9yd44t====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuc6tm18-9yd44t exit=${code}====="
exit "$code"
