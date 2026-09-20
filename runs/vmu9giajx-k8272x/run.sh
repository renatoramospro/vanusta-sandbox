#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9giajx-k8272x====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9giajx-k8272x exit=${code}====="
exit "$code"
