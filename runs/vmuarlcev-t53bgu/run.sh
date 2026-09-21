#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuarlcev-t53bgu====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuarlcev-t53bgu exit=${code}====="
exit "$code"
