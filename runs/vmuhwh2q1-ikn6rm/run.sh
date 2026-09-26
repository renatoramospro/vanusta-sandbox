#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhwh2q1-ikn6rm====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhwh2q1-ikn6rm exit=${code}====="
exit "$code"
