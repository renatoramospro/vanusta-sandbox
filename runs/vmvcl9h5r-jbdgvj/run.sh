#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcl9h5r-jbdgvj====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcl9h5r-jbdgvj exit=${code}====="
exit "$code"
