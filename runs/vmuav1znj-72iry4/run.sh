#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuav1znj-72iry4====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuav1znj-72iry4 exit=${code}====="
exit "$code"
