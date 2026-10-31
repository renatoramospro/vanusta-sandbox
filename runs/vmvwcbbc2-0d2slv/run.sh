#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvwcbbc2-0d2slv====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvwcbbc2-0d2slv exit=${code}====="
exit "$code"
