#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmve40r3t-g94c2k====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmve40r3t-g94c2k exit=${code}====="
exit "$code"
