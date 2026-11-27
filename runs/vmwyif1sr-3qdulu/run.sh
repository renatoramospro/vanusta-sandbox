#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwyif1sr-3qdulu====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwyif1sr-3qdulu exit=${code}====="
exit "$code"
