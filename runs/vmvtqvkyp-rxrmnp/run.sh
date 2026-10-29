#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvtqvkyp-rxrmnp====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvtqvkyp-rxrmnp exit=${code}====="
exit "$code"
