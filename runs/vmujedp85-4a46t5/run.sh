#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujedp85-4a46t5====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujedp85-4a46t5 exit=${code}====="
exit "$code"
