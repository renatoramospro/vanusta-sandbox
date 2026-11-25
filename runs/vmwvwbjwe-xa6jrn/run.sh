#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwvwbjwe-xa6jrn====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwvwbjwe-xa6jrn exit=${code}====="
exit "$code"
