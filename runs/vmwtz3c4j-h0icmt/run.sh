#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwtz3c4j-h0icmt====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwtz3c4j-h0icmt exit=${code}====="
exit "$code"
