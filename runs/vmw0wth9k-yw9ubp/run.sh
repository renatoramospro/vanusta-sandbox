#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmw0wth9k-yw9ubp====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmw0wth9k-yw9ubp exit=${code}====="
exit "$code"
