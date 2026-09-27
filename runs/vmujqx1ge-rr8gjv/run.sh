#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujqx1ge-rr8gjv====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujqx1ge-rr8gjv exit=${code}====="
exit "$code"
