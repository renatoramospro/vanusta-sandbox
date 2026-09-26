#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuik1xxx-k0c6jk====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuik1xxx-k0c6jk exit=${code}====="
exit "$code"
