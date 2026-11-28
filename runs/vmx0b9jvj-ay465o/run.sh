#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmx0b9jvj-ay465o====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmx0b9jvj-ay465o exit=${code}====="
exit "$code"
