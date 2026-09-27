#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuju92em-6iwi2k====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuju92em-6iwi2k exit=${code}====="
exit "$code"
