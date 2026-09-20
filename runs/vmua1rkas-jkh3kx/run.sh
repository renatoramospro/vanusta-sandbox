#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua1rkas-jkh3kx====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua1rkas-jkh3kx exit=${code}====="
exit "$code"
