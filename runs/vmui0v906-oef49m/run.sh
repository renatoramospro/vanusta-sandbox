#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmui0v906-oef49m====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmui0v906-oef49m exit=${code}====="
exit "$code"
