#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuibhbzo-vptg0u====="
(
  set -e
  python 'dependency_resolver.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuibhbzo-vptg0u exit=${code}====="
exit "$code"
