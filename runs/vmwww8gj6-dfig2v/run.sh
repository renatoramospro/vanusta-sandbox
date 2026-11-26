#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwww8gj6-dfig2v====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwww8gj6-dfig2v exit=${code}====="
exit "$code"
