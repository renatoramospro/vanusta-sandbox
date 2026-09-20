#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuac2pck-fufppo====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuac2pck-fufppo exit=${code}====="
exit "$code"
