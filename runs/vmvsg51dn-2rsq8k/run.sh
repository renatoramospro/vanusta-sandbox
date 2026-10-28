#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvsg51dn-2rsq8k====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvsg51dn-2rsq8k exit=${code}====="
exit "$code"
