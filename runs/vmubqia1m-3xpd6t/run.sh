#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubqia1m-3xpd6t====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubqia1m-3xpd6t exit=${code}====="
exit "$code"
