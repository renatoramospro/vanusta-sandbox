#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmugv75yr-60z70k====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmugv75yr-60z70k exit=${code}====="
exit "$code"
