#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9vf220-10x09j====="
(
  set -e
  python 'container.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9vf220-10x09j exit=${code}====="
exit "$code"
