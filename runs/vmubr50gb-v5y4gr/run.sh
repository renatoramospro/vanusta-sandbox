#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubr50gb-v5y4gr====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubr50gb-v5y4gr exit=${code}====="
exit "$code"
