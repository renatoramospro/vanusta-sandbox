#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhx82ak-uzs99o====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhx82ak-uzs99o exit=${code}====="
exit "$code"
