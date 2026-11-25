#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwwe4mvd-sdldmw====="
(
  set -e
  python 'build_system.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwwe4mvd-sdldmw exit=${code}====="
exit "$code"
