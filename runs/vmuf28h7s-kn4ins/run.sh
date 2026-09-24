#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuf28h7s-kn4ins====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest 'pydantic>=2.0.0' 'PyYAML>=6.0'
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuf28h7s-kn4ins exit=${code}====="
exit "$code"
