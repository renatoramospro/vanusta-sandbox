#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujbldoq-da9gkg====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujbldoq-da9gkg exit=${code}====="
exit "$code"
