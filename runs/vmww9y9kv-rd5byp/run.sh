#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmww9y9kv-rd5byp====="
(
  set -e
  python 'pathfinder.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmww9y9kv-rd5byp exit=${code}====="
exit "$code"
