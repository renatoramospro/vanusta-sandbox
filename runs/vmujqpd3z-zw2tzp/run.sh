#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujqpd3z-zw2tzp====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujqpd3z-zw2tzp exit=${code}====="
exit "$code"
