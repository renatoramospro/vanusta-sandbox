#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmub9u0vr-o042ou====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmub9u0vr-o042ou exit=${code}====="
exit "$code"
