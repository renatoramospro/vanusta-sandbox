#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcll1ar-93nj9m====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcll1ar-93nj9m exit=${code}====="
exit "$code"
