#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvkvtuda-qfqjop====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvkvtuda-qfqjop exit=${code}====="
exit "$code"
