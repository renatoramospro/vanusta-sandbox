#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwwvwwpl-cloajj====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwwvwwpl-cloajj exit=${code}====="
exit "$code"
