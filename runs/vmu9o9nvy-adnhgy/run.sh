#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9o9nvy-adnhgy====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9o9nvy-adnhgy exit=${code}====="
exit "$code"
