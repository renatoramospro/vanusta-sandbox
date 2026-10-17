#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcn6wnt-im8s1g====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcn6wnt-im8s1g exit=${code}====="
exit "$code"
