#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuatjhix-e4320h====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuatjhix-e4320h exit=${code}====="
exit "$code"
