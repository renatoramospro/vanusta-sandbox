#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcy0f6l-bw689b====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcy0f6l-bw689b exit=${code}====="
exit "$code"
