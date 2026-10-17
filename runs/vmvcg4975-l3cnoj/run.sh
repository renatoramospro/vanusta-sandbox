#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcg4975-l3cnoj====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcg4975-l3cnoj exit=${code}====="
exit "$code"
