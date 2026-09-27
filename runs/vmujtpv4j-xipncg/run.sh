#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujtpv4j-xipncg====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujtpv4j-xipncg exit=${code}====="
exit "$code"
