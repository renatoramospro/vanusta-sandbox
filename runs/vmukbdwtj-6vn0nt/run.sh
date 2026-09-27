#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukbdwtj-6vn0nt====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukbdwtj-6vn0nt exit=${code}====="
exit "$code"
