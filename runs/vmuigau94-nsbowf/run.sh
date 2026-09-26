#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuigau94-nsbowf====="
(
  set -e
  python 'di_container.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuigau94-nsbowf exit=${code}====="
exit "$code"
