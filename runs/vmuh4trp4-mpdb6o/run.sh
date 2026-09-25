#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuh4trp4-mpdb6o====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuh4trp4-mpdb6o exit=${code}====="
exit "$code"
