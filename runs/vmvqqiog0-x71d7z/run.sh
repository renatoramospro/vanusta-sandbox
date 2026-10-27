#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvqqiog0-x71d7z====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvqqiog0-x71d7z exit=${code}====="
exit "$code"
