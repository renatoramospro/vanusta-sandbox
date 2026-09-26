#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuicvhut-4m2s27====="
(
  set -e
  python 'dependency_resolver.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuicvhut-4m2s27 exit=${code}====="
exit "$code"
