#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcbeilp-q2le0z====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcbeilp-q2le0z exit=${code}====="
exit "$code"
