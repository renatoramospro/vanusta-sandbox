#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuj4b15q-blrzut====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuj4b15q-blrzut exit=${code}====="
exit "$code"
