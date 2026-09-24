#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmug6n9u8-uozbia====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmug6n9u8-uozbia exit=${code}====="
exit "$code"
