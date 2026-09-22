#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucphdbu-qs57pi====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucphdbu-qs57pi exit=${code}====="
exit "$code"
