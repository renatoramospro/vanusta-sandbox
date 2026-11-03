#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmw0mym5n-swgfmt====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmw0mym5n-swgfmt exit=${code}====="
exit "$code"
