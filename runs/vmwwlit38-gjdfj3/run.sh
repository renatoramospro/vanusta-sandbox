#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwwlit38-gjdfj3====="
(
  set -e
  python 'dependency_resolver.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwwlit38-gjdfj3 exit=${code}====="
exit "$code"
