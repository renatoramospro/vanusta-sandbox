#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvzh9oob-5a7q2m====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvzh9oob-5a7q2m exit=${code}====="
exit "$code"
