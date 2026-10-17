#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcetugw-k2mt0m====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcetugw-k2mt0m exit=${code}====="
exit "$code"
