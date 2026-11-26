#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwwu3qjf-jasg8o====="
(
  set -e
  python 'broker.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwwu3qjf-jasg8o exit=${code}====="
exit "$code"
