#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmui16vgo-zuy6rr====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmui16vgo-zuy6rr exit=${code}====="
exit "$code"
