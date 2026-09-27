#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukdb94j-vkrbh1====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukdb94j-vkrbh1 exit=${code}====="
exit "$code"
