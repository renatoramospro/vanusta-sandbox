#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuky3vsq-9306tm====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuky3vsq-9306tm exit=${code}====="
exit "$code"
