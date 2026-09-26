#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmui30frh-bc02cn====="
(
  set -e
  python 'lzw.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmui30frh-bc02cn exit=${code}====="
exit "$code"
