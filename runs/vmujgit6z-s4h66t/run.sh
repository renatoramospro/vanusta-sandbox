#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujgit6z-s4h66t====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujgit6z-s4h66t exit=${code}====="
exit "$code"
