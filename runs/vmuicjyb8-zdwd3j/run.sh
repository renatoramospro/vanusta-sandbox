#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuicjyb8-zdwd3j====="
(
  set -e
  python 'dependency_resolver.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuicjyb8-zdwd3j exit=${code}====="
exit "$code"
