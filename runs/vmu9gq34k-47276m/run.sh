#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9gq34k-47276m====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9gq34k-47276m exit=${code}====="
exit "$code"
