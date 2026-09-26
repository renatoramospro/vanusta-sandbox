#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuibswb3-vra4so====="
(
  set -e
  python 'dependency_resolver.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuibswb3-vra4so exit=${code}====="
exit "$code"
