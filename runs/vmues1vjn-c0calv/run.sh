#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmues1vjn-c0calv====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmues1vjn-c0calv exit=${code}====="
exit "$code"
