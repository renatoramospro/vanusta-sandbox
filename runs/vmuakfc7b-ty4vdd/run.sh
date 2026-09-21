#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuakfc7b-ty4vdd====="
(
  set -e
  python 'persistence_system.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuakfc7b-ty4vdd exit=${code}====="
exit "$code"
