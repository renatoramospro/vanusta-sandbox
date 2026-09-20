#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua3mgy7-ahm0ud====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua3mgy7-ahm0ud exit=${code}====="
exit "$code"
