#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmufe0yjq-46sw3p====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmufe0yjq-46sw3p exit=${code}====="
exit "$code"
