#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhhkpvb-bryqy8====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhhkpvb-bryqy8 exit=${code}====="
exit "$code"
