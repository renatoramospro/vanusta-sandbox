#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukxoeyx-6glh92====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukxoeyx-6glh92 exit=${code}====="
exit "$code"
