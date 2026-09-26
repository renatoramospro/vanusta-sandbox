#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmui1xvln-ark5h8====="
(
  set -e
  python 'lzw.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmui1xvln-ark5h8 exit=${code}====="
exit "$code"
